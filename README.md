# Onani

A booru-style imageboard built with **Flask** (API) and **Vue 3** (SPA).

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask + Gunicorn, Flask-RESTful |
| Frontend | Vue 3 + Vite SPA |
| Database | PostgreSQL 14 |
| Cache / Queue | Redis 7 + Celery 5 |
| Container runtime | Podman + podman-compose |

## Quick Start

### 1. Generate environment

```bash
./generate_env.sh
```

Generates `.env` with `FLASK_SECRET_KEY` and `DB_PASSWORD`. 

For production, you only need these two variables. Optional host-path variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `IMAGES_HOST_DIR` | `./images` | Uploaded post media |
| `AVATARS_HOST_DIR` | `./avatars` | User avatars |
| `DATABASE_HOST_DIR` | `./database` | PostgreSQL data |
| `VERSION` | `latest` | Image tag (e.g. `v1.0.0`, `sha-abcd1234`) |
| `REGISTRY` | `ghcr.io/onani-dev/onani` | Override GHCR registry |
| `PORT` | `80` | HTTP port (prod only) |

### 2. Start services

Choose one profile set depending on whether you want ML dependencies baked into containers.

**Development (no ML)** (Flask debug + Vite hot reload, local builds):

```bash
podman-compose --profile dev up -d --build
```

**Development (ML-enabled)** (includes `requirements-ml.txt` in Flask/Celery images):

```bash
podman-compose --profile dev-ml up -d --build
```

| URL | Service |
|-----|---------|
| http://localhost:5173 | Vue SPA (Vite) |
| http://localhost:5000 | Flask API |

**Production (no ML)** (all-in-one: Gunicorn + Caddy, pre-built from GHCR):

```bash
podman-compose --profile prod up -d
```

Pulls pre-built images `ghcr.io/onani-dev/onani-app` and `ghcr.io/onani-dev/onani-celery` (tagged `latest`, or override with `VERSION=v1.0.0`).

| URL | Service |
|-----|---------|
| http://localhost | App (Caddy → Gunicorn + Vue SPA) |

**Production (ML-enabled)** (pre-built ML GHCR images: `app-ml`, `celery-ml`):

```bash
podman-compose --profile prod-ml up -d
```

Override port: `PORT=8080 podman-compose --profile prod up -d`

### 3. Seed and first admin

```bash
# Seed default tags
flask tags --filename meta.json
flask tags --filename explicit.json

# Promote a registered user to owner
flask add-owner --id <USER_ID>
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init-db` | Create database tables |
| `tags --filename FILE` | Seed tags from a JSON file |
| `add-owner --id ID` | Promote user to owner |
| `reset-password --id ID` | Reset a user's password |
| `disable-otp --id ID` | Disable 2FA for a user |
| `db migrate` | Generate Alembic migration |
| `db upgrade` | Apply pending migrations |

Via compose: `podman-compose ... exec flask flask <command>`

## Optional: DeepDanbooru Setup

If admin DeepDanbooru tasks show:

`Python package 'deepdanbooru' is not installed.`

install the ML dependencies from `requirements-ml.txt`.

### Local (nix + venv)

```bash
nix develop --command .venv/bin/pip install -r requirements-ml.txt
```

If you run Flask directly from your shell/venv, this is enough.

### Dev container (`flask-dev` / `celery-dev`)

Quick install into running containers:

```bash
podman-compose --profile dev exec flask-dev pip install -r /onani/requirements-ml.txt
podman-compose --profile dev exec celery-dev pip install -r /onani/requirements-ml.txt
```

This works immediately, but is not persistent across image rebuilds.

Persistent install for future rebuilds:

1. Add `-r requirements-ml.txt` to `requirements.txt` (or copy those packages into `requirements.txt`).
2. Rebuild dev images:

```bash
podman-compose --profile dev up -d --build
```

### Enable and configure DeepDanbooru

Set configuration (either env vars or `onani.toml`):

- `DEEPDANBOORU_ENABLED=true`
- `DEEPDANBOORU_PROJECT_PATH=/models/deepdanbooru`

In dev compose, the default bind mount is:

- `${DEEPDANBOORU_MODEL_HOST_DIR:-./models/deepdanbooru}:/models/deepdanbooru:ro`

So place your model files in `./models/deepdanbooru` by default.

### Where to get DeepDanbooru weights

Onani does not ship DeepDanbooru weights. You need either:

- A trained DeepDanbooru project you created yourself, or
- A compatible pre-trained model package from a community source.

Common places to find compatible weights:

- DeepDanbooru project/resources: https://github.com/KichangKim/DeepDanbooru
- Hugging Face model search: https://huggingface.co/models?search=deepdanbooru

For `DEEPDANBOORU_PROJECT_PATH`, the directory should contain:

- `project.json`
- `tags.txt`
- A model file (for example `.keras`, `.h5`, or SavedModel exported by your package)

If your package only provides separate model and tags files, configure:

- `DEEPDANBOORU_MODEL_PATH=/models/deepdanbooru/<model-file>`
- `DEEPDANBOORU_TAGS_PATH=/models/deepdanbooru/tags.txt`

## Testing

```bash
nix develop --command .venv/bin/pytest
```

Tests use an in-memory SQLite database and mock Redis — no running containers needed.

## Releases

Version source of truth is the `VERSION` file.

Sync version files only:

```bash
./scripts/sync-version.sh --bump-beta
```

Other bump modes:

```bash
./scripts/sync-version.sh --bump-patch
./scripts/sync-version.sh --bump-minor
./scripts/sync-version.sh --bump-major
```

Set an explicit version:

```bash
./scripts/sync-version.sh --set 1.1.0-beta.1
```

Create commit + tag + push:

```bash
./scripts/release.sh --bump-beta
```

For stable releases you can use semantic bumps, for example:

```bash
./scripts/release.sh --bump-patch
```

Create commit + tag without pushing:

```bash
./scripts/release.sh --bump-beta --no-push
```

Releases are tag-driven. Pushing a `v*` tag creates a GitHub Release and publishes container images (`app`, `celery`) to GHCR. Tags matching `*-beta.*` are marked as prereleases.

Container image publishing runs on tag pushes (and manual dispatch), not on regular branch pushes.

## License

Proprietary — Sanvia Digital LTD. See [LICENSE](LICENSE) for details.