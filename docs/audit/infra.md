# Infra / Supply Chain Audit

Read-only audit. Only verified findings (each traced to a specific file/line).

## Findings

### High

1. **Containers run as root — no `USER` directive**
   - `Dockerfile:1-60`, `Dockerfile.dev:1-30`, `celery/dockerfile:1-41`, `celery/dockerfile.dev:1-32`
   - Problem: none of the four images declare a non-root `USER`. Gunicorn, the dev Flask server, cron, and the Celery worker all run as root inside the container. `docker-compose.yml` doesn't set `user:` either. A code-exec bug (e.g. in the image-processing/deepdanbooru pipeline) gets root in-container immediately, and cron running as root (`entrypoints/entrypoint.sh:36-43`) widens that further.
   - Fix: add an unprivileged user (`RUN adduser -D app` / `useradd`), `chown` the app dirs it needs to write (`/onani`, `/logs`, `/static`), and `USER app` before `ENTRYPOINT`. Gunicorn binds to `127.0.0.1:8000` (unprivileged port) and Caddy binds `:80` — port 80 needs `setcap cap_net_bind_service` on the caddy binary or switching to `:8080` + host port mapping, since a non-root user can't bind to it directly.
   - Effort: M (touches all 4 Dockerfiles + the `:80` bind in `caddy/Caddyfile` / compose port mapping).

2. **Postgres port published to the host in the primary compose file**
   - `docker-compose.yml:196-197` (`ports: - 5432:5432` on the `postgres` service)
   - Problem: Postgres is reachable directly from the host network (and from any container/VM that can reach the host), bypassing the app entirely. `docker-compose.example.yml`'s `postgres` service correctly has no `ports:` block — the shipped example is safer than the repo's own dev/prod compose file. Combined with the default `DB_PASSWORD: onani_db` used in the `dev` profile (`docker-compose.yml:14`), a local/LAN attacker can connect with `psql -h <host> -U onani_db -d onani_db` using a well-known default password.
   - Fix: drop the `5432:5432` port mapping (Postgres only needs to be reachable from `app`/`celery` over the compose network); if host access is needed for admin/backup, bind to `127.0.0.1:5432:5432` instead of all interfaces.
   - Effort: S.

### Medium

3. **Weak default credentials for dev profile**
   - `docker-compose.yml:14-15` (`DB_PASSWORD: ${DB_PASSWORD:-onani_db}`, `DEFAULT_ADMIN_PASSWORD: ${DEFAULT_ADMIN_PASSWORD:-admin}`)
   - Problem: if `.env` isn't populated (e.g. `generate_env.sh` skipped), `dev`/`dev-ml` profiles boot with DB password `onani_db` and app admin password `admin`. Combined with finding #2 (exposed 5432) and no auth in front of Postgres beyond the password, this is a real exposure for anyone running `--profile dev` on a shared/LAN host. Acceptable as a *pure local* dev convenience, but worth a loud warning since the compose file doesn't gate it.
   - Fix: keep the defaults for pure-local dev but only if #2 is fixed (bind 127.0.0.1 or no publish); consider a startup check that refuses `DEFAULT_ADMIN_PASSWORD=admin` when `FLASK_ENV != development`.
   - Effort: S.

4. **No security headers in Caddyfile**
   - `caddy/Caddyfile:1-20`
   - Problem: no `header` directive at all — missing `X-Content-Type-Options`, `X-Frame-Options`/`frame-ancestors`, `Referrer-Policy`, and a CSP. The SPA and reverse-proxied API responses go out with Caddy's bare defaults.
   - Fix: add a `header` block, e.g.:
     ```
     header {
         X-Content-Type-Options nosniff
         X-Frame-Options DENY
         Referrer-Policy strict-origin-when-cross-origin
         -Server
     }
     ```
     (`auto_https off` at line 2 is fine — this app is meant to sit behind an external TLS terminator per the compose port mapping — but the internal proxy should still not leak `Server` headers and should set the above.)
   - Effort: S.

5. **All Python dependencies are floor-pinned (`>=`) only, no lockfile**
   - `requirements.txt:1-46`, `requirements-ml.txt:1-6`
   - Problem: every line uses `>=` with no upper bound and there is no `requirements.lock`/`pip-compile` output, so `pip3 install -r requirements.txt` (`Dockerfile:44`, `Dockerfile.dev:17`, `celery/dockerfile:26`, `celery/dockerfile.dev:17`) resolves to whatever is newest at build time — different environments/build dates can silently get different dependency graphs, and a compromised/broken upstream release ships straight into the image with no pin to roll back to. (Recent history shows this already bit the project: commit `9ae1f2f "fix: pin tensorflow-cpu==2.14 ... remove Dockerfile workaround"` pinned TF at ==2.14 to work around a breakage, but `requirements-ml.txt:5` currently reads `tensorflow-cpu>=2.16`, i.e. the exact-pin was later loosened back to an open range.)
   - `pip-audit` was requested but is not installed in this environment (`pip-audit: command not found`) — skipped per instructions; dependency CVEs were not checked, only the pinning practice.
   - Fix: generate a lock file (`pip-compile`/`uv pip compile`) and install from that in the Dockerfiles; keep `requirements.txt` as the abstract spec.
   - Effort: M.

6. **npm audit: 4 high-severity vulnerabilities in frontend deps**
   - `frontend/package.json`, `frontend/package-lock.json` (`npm audit --omit=dev` run in `frontend/`)
   - Findings: `axios` (11 advisories — prototype pollution / SSRF / DoS family, via transitive/old axios resolution), `form-data` 4.0.0–4.0.5 (CRLF injection, high), `nanoid` ≤3.3.17 (predictable/looping ID generation, high), `postcss` ≤8.5.22 (arbitrary file read via sourceMappingURL, high). `npm audit fix` reports a fix is available for all four.
   - Fix: run `npm audit fix` in `frontend/`, commit the updated lockfile, re-run `npm run build` to confirm no breakage.
   - Effort: S.

### Low

7. **`app`/`celery`/`app-ml`/`celery-ml` services have no healthcheck**
   - `docker-compose.yml:136-187`
   - Problem: `postgres` (line 205) and `redis` (line 214) have healthchecks and are correctly used as `depends_on: condition: service_healthy` (`docker-compose.yml:30-34`), but the app/celery services themselves have none, so `restart: unless-stopped` and any external orchestration can't detect a wedged Gunicorn/Celery process short of the container exiting outright.
   - Fix: add a `healthcheck` hitting `/api/health` (or similar) for `app`, and a `celery inspect ping` healthcheck for the celery services.
   - Effort: S.

8. **`celery-ml` has a duplicated volume mount**
   - `docker-compose.yml:186-187` — `${DEEPDANBOORU_MODEL_HOST_DIR:-./models/deepdanbooru}:/models/deepdanbooru:ro` is listed twice.
   - Problem: harmless (compose just mounts it twice) but is copy-paste debris and a sign this file isn't being lint-checked.
   - Fix: delete the duplicate line.
   - Effort: S.

9. **`gunicorn -w 10 --threads 100`** (`entrypoints/entrypoint.sh:50`)
   - 10 workers × 100 threads = up to 1000 concurrently-accepted requests per `app` container with default settings; combined with running as root (#1) and no resource limits set anywhere in `docker-compose.yml`, a burst of slow/malicious requests can exhaust host memory. Not exploitable per se, but worth a second look — this is unusually high for a booru-style app and has no accompanying `--timeout`/`-max-requests` tuning.
   - Fix: benchmark actual concurrency needs; add `--timeout`, `--max-requests`/`--max-requests-jitter`, and a compose-level `mem_limit`/`deploy.resources.limits` for the `app` service.
   - Effort: M (needs load-testing to size correctly, not just a config tweak).

## Not flagged / verified clean

- **CI workflows** (`.github/workflows/container-builds.yml`, `release.yml`): `permissions:` blocks are least-privilege (`contents: read, packages: write` / `contents: write` only), no untrusted PR input (titles, branch names, issue bodies) is interpolated into any `run:` shell block — the only dynamic values used in shell are `GITHUB_REPOSITORY_OWNER`/`GITHUB_REPOSITORY` (trusted context) — and secrets (`GITHUB_TOKEN`) are only passed via `env:`, never string-interpolated into a command. No injection risk found.
- **`.dockerignore`**: excludes `.env`, `.git`, `docker-compose*`, `Dockerfile*` from the build context — no secrets get baked into image layers via context copy.
- **`generate_env.sh`**: generates `DB_PASSWORD`/`FLASK_SECRET_KEY` from `/dev/urandom` with adequate length (20 alnum chars / 32 bytes hex) — good default for prod path.
- **`redis`**: no port published to host in `docker-compose.yml` (correctly internal-only), has a healthcheck.
- **Multi-stage builds / layer caching**: `Dockerfile` already multi-stages the frontend build and pulls the Caddy binary via `COPY --from=caddy`, and puts `COPY requirements.txt ...` + `pip install` before `COPY . /onani` — dependency layer is correctly cached ahead of app-code changes. No quick win identified here beyond alpine/slim variant choice, which is already deliberate (see the `INSTALL_ML` comment at `Dockerfile:1-2`).
- **`pip-audit`**: not installed in this environment; skipped as instructed rather than guessed at.

## Summary

Audited Dockerfiles (4), docker-compose files (2), Caddyfile, entrypoint scripts (4), build/env scripts, CI workflows (2), and dependency manifests (Python + frontend). Ran `npm audit` (4 high findings); `pip-audit` unavailable, skipped. Biggest risks: all containers run as root with no `USER` directive, and Postgres's 5432 is published to the host alongside a weak default dev password — those two compound into a real exposure on any shared/LAN dev box.

**Findings by severity: High: 2, Medium: 4, Low: 3.**
