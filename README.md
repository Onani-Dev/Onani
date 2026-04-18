# Onani

A booru-style imageboard built with **Flask** (API) and **Vue 3** (SPA frontend).

## Architecture

```
Onani/
├── services/       ← Pure business logic (no Flask globals)
├── controllers/    ← Route decorators + backward-compat shim
├── models/         ← SQLAlchemy models + Marshmallow schemas
├── routes/
│   ├── api/v1/     ← REST API (Flask-RESTful)
│   ├── auth/       ← Legacy server-rendered auth
│   ├── views/      ← Legacy Jinja2 views
│   └── spa.py      ← SPA catch-all (/)
├── importers/      ← gallery-dl importer (900+ sites)
├── tasks/          ← Celery async tasks
└── cron/           ← Scheduled jobs

frontend/           ← Vue 3 + Vite SPA
```

### Service layer (`Onani/services/`)

All database and business logic lives here as plain Python — no Flask
request/response, `current_user`, `flash()`, or `abort()` calls. Services
accept explicit parameters (the acting user, config values) and raise typed
exceptions (`BanError`, `InvalidCredentialsError`, etc.) that route handlers
catch and translate into HTTP responses.

### API (`/api/v1/`)

| Endpoint group             | Methods               | Auth required |
| -------------------------- | --------------------- | ------------- |
| `/auth/login`              | POST                  | No            |
| `/auth/logout`             | POST                  | Yes           |
| `/auth/register`           | POST                  | No            |
| `/auth/me`                 | GET                   | No (returns auth status) |
| `/auth/csrf`               | GET                   | No            |
| `/posts`                   | GET                   | No            |
| `/post`                    | GET, PUT, PATCH       | PUT/PATCH: Yes |
| `/posts/vote`              | POST                  | Yes           |
| `/posts/upload`            | POST                  | Yes           |
| `/comments`                | GET, POST, DELETE     | POST/DELETE: Yes |
| `/tags`                    | GET                   | No            |
| `/tags/autocomplete`       | GET                   | No            |
| `/news`                    | GET                   | No            |
| `/users`                   | GET                   | Yes           |
| `/users/posts`             | GET                   | No            |
| `/collections`             | GET, POST, PUT, DELETE | POST/PUT/DELETE: Yes |
| `/collections/posts`       | POST, DELETE          | Yes           |
| `/profile`                 | GET, PUT, PATCH       | Yes           |
| `/import`                  | GET, POST             | Yes (perm)    |
| `/admin/stats`             | GET                   | Yes (moderator) |
| `/admin/errors`            | GET                   | Yes (view logs perm) |
| `/admin/celery-logs`       | GET                   | Yes (view logs perm) |
| `/admin/run-task`          | POST                  | Yes (admin)   |
| `/admin/ban`               | POST, DELETE          | Yes (perm)    |
| `/admin/news`              | POST                  | Yes (perm)    |

Authentication uses Flask-Login session cookies. The SPA bootstraps a CSRF
token from `/auth/csrf` and sends it on mutating requests via the
`X-CSRFToken` header.

### Frontend (`frontend/`)

Vue 3 SPA served at the root (`/`). Built with:

- **Vite** — build tooling
- **Vue Router 4** — client-side routing (HTML5 history mode)
- **Pinia** — state management (auth store)
- **Axios** — HTTP client with CSRF interceptor

In development, Vite's dev server proxies `/api` and `/static` to Flask on
port 5000.

## Running

### Prerequisites

You need **one** of the following:

- **Docker** + **Docker Compose** — everything runs in containers
- **Nix** — `flake.nix` provides a complete dev shell
- **Manual** — Python 3.10+, Node.js 22+, PostgreSQL 14, Redis 7, ffmpeg

### 1. Generate environment file

```bash
python generate_env.py
```

The script generates a `.env` with `DB_PASSWORD` and `FLASK_SECRET_KEY`.

### 2a. Docker — production

```bash
./build.sh
```

This builds and starts all six services. The Flask entrypoint automatically
runs `flask db init`, `flask init-db`, and `flask db migrate` before
starting gunicorn. Once healthy:

| URL | What |
| --- | ---- |
| http://localhost:8080/ | Vue SPA (via nginx) |
| http://localhost:8080/api/v1/ | REST API (via nginx → gunicorn) |

Seed default tags:

```bash
docker exec -it onani_flask flask tags --filename meta.json
docker exec -it onani_flask flask tags --filename explicit.json
```

Create an admin user:

```bash
docker exec -it onani_flask flask add-owner --id <USER_ID>
```

### 2b. Docker — development

```bash
./build.sh dev
```

Same as production, but:

- Source code is bind-mounted (`./:/onani`) — gunicorn runs with `--reload`
- Flask is exposed directly on **:5000** (bypass nginx)
- PostgreSQL on **:5432** and Redis on **:6379** are exposed to the host
- `FLASK_ENV=development`, `TESTING=True`, SQL echo on
- Cron jobs are started (`crond` + `flask crontab add`)
- The **frontend container is not included**

To work on the Vue SPA during development, run Vite separately:

```bash
cd frontend
npm install
npm run dev          # starts on :5173, proxies /api + /static → Flask :5000
```

| URL | What |
| --- | ---- |
| http://localhost:5173/ | Vue SPA (Vite dev server, hot reload) |
| http://localhost:5000/api/v1/ | Flask API direct |
| http://localhost:8080/ | nginx (production-like) |

### 2c. Nix — fully local (no Docker)

```bash
nix develop                       # enters dev shell with Python, Node, ffmpeg, etc.
pip install -r requirements.txt   # Python deps into .venv (auto-created)
```

You need PostgreSQL and Redis running locally (or use Docker just for those):

```bash
# Option A: start just Postgres + Redis via Docker
docker compose up -d postgres redis

# Option B: use system services
# Make sure DATABASE_URL points to your local Postgres
```

Then start the backend and frontend in separate terminals:

```bash
# Terminal 1 — Flask
export DATABASE_URL=postgresql://onani_db:onani_db@localhost:5432/onani_db
flask run                         # starts on :5000

# Terminal 2 — Vue
cd frontend && npm install && npm run dev   # starts on :5173
```

## CLI Commands

Run via `flask <command>` (or `docker exec -it onani_flask flask <command>`):

| Command                          | Description                     |
| -------------------------------- | ------------------------------- |
| `init-db`                        | Create database tables          |
| `drop-db`                        | Drop and recreate tables (testing only) |
| `tags --filename FILE`           | Seed tags from a defaults JSON  |
| `add-owner --id ID`              | Promote user to owner role      |
| `reset-password --id ID`         | Reset a user's password         |
| `disable-otp --id ID`            | Disable 2FA for a user          |
| `db init`                        | Initialize migrations directory |
| `db migrate`                     | Generate Alembic migration      |
| `db upgrade`                     | Apply pending migrations        |

## Docker Services

| Service    | Ports (dev) | Purpose                           |
| ---------- | ----------- | --------------------------------- |
| `flask`    | 5000        | API + legacy views (gunicorn)     |
| `nginx`    | 8080        | Reverse proxy, static files, SPA  |
| `postgres` | 5432        | PostgreSQL 14                     |
| `redis`    | 6379        | Cache + Celery broker             |
| `celery`   | —           | Async task workers (10 concurrent)|
| `frontend` | —           | Vue build (production only)       |

Both modes use the same `docker-compose.yml` — `./build.sh` activates the
`prod` profile, `./build.sh dev` activates `dev`. Postgres and Redis are
shared; Flask, nginx, and celery have profile-specific variants.

## Environment Variables

Set in `.env` (generated by `generate_env.py`):

| Variable                | Required | Description                |
| ----------------------- | -------- | -------------------------- |
| `FLASK_SECRET_KEY`      | Yes      | Session signing key        |
| `DB_PASSWORD`           | Yes      | PostgreSQL password        |
| `DATABASE_URL`          | No       | SQLAlchemy database URI    |
| `IMAGES_DIR`            | No       | Post image storage path    |
| `AVATARS_DIR`           | No       | Avatar storage path        |
| `GALLERY_DL_CONFIG_FILE`| No       | gallery-dl config path     |
| `CELERY_BROKER_URL`     | No       | Celery broker URL          |
| `RATELIMIT_STORAGE_URI` | No       | Rate limiter backend       |
| `RATELIMIT_ENABLED`     | No       | Set `False` to disable     |

## Testing

```bash
pip install -r requirements-dev.txt
DATABASE_URL=sqlite:///:memory: FLASK_SECRET_KEY=test \
  RATELIMIT_STORAGE_URI=memory:// RATELIMIT_ENABLED=False \
  python -m pytest tests/ -q
```

## License

Proprietary — Sanvia Digital LTD. See [LICENSE](LICENSE) for details.