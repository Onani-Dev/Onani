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
python generate_env.py
```

Generates `.env` with `FLASK_SECRET_KEY` and `DB_PASSWORD`. 

For production, you only need these two variables. Optional host-path variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `IMAGES_HOST_DIR` | `./images` | Uploaded post media |
| `AVATARS_HOST_DIR` | `./avatars` | User avatars |
| `DATABASE_HOST_DIR` | `./database` | PostgreSQL data |
| `VERSION` | `latest` | Image tag (e.g. `v1.0.0`, `sha-abcd1234`) |
| `REGISTRY` | `ghcr.io/kapsikkum/onani` | Override GHCR registry |
| `PORT` | `80` | HTTP port (prod only) |

### 2. Start services

**Development** (Flask debug + Vite hot reload, local builds):

```bash
podman-compose --profile dev up -d --build
```

| URL | Service |
|-----|---------|
| http://localhost:5173 | Vue SPA (Vite) |
| http://localhost:5000 | Flask API |

**Production** (all-in-one: Gunicorn + Caddy, pre-built from GHCR):

```bash
podman-compose --profile prod up -d
```

Pulls pre-built images `ghcr.io/kapsikkum/onani-app` and `ghcr.io/kapsikkum/onani-celery` (tagged `latest`, or override with `VERSION=v1.0.0`).

| URL | Service |
|-----|---------|
| http://localhost | App (Caddy → Gunicorn + Vue SPA) |

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

Create commit + tag + push:

```bash
./scripts/release.sh --bump-beta
```

Releases are tag-driven. Pushing a `v*` tag creates a GitHub Release and publishes container images (`app`, `celery`) to GHCR. Tags matching `*-beta.*` are marked as prereleases.

## License

Proprietary — Sanvia Digital LTD. See [LICENSE](LICENSE) for details.