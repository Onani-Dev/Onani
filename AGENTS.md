# Development Workflow

## Running the Dev Server

Use Podman Compose profiles as the primary workflow.

There are two main modes:

1. `prod` mode: Gunicorn + Flask production stack.
2. `dev` mode: Flask debug server + Vite dev server.

```sh
# Start all dev services (Flask debug on :5000, Vite on :5173, Postgres, Redis, Celery)
podman-compose -f docker-compose.yml --profile dev up -d --build
```

```sh
# Start production-mode app services (Gunicorn on :5000, Postgres, Redis, Celery)
podman-compose -f docker-compose.yml --profile prod up -d --build
```

- Flask API: http://localhost:5000
- Vite SPA: http://localhost:5173
- Source code is volume-mounted, so changes hot-reload without rebuilding.
- In-repo nginx is optional (`proxy` profile) and not required for normal prod/dev modes.
- **Celery does not auto-reload.** After any change to `Onani/tasks/`, `celery_worker.py`, or anything imported by the worker, restart it manually:
  ```sh
  podman restart onani_celery-dev_1
  ```

### Manual run (fallback)

If needed, you can run services manually outside compose:

```sh
# Backend dev mode
flask run --host=0.0.0.0 --port=5000 --debug

# Frontend dev mode (separate terminal)
cd frontend && npm run dev
```

```sh
# Backend production-style run
gunicorn -b 0.0.0.0:5000 -w 10 --threads 100 run:app
```

## Testing Requirements

- **Run `pytest` inside `nix develop`** after meaningful backend changes (logic, new behaviour, bug fixes). Trivial changes like variable renames or comment edits do not require a test run.
  ```sh
  nix develop --command .venv/bin/pytest
  ```
- **Update existing tests** when changing behaviour — never leave tests that contradict the new code.
- **Add new tests** for any new route, service function, model method, or utility.
- Tests live in `tests/`, follow the `test_*.py` / `Test*` / `test_*` naming conventions from `pytest.ini`.
- Tests use an in-memory SQLite database and mock Redis — no running containers are needed.

---

# Project Rundown

## What the App Does

**Onani** is a booru-style imageboard/content aggregation platform (similar to Danbooru/Rule34) built with **Flask** (REST API) and **Vue 3** (SPA). Key capabilities:

- Upload images/videos with metadata (source URL, description, tags, rating)
- Browse and search posts by tags with tag filtering/exclusion
- Vote on posts (upvote, downvote) and "water" (like/favourite) posts
- Create and manage collections of posts
- Import content from 900+ external sites via gallery-dl
- Write and read news/announcements
- Manage user profiles (avatar, bio, social links, custom CSS)
- Apply SFW mode to blur explicit content
- Role-based access control with granular bitmask permissions
- Rate content as General / Questionable / Explicit

---

## Architecture Overview

| Layer | Technology |
|-------|-----------|
| Backend API | Flask 2.3+ with Flask-RESTful |
| ORM | SQLAlchemy 1.4 + Flask-SQLAlchemy |
| Serialisation | Marshmallow + marshmallow-SQLAlchemy |
| Auth | Flask-Login (sessions) + Argon2 passwords + TOTP (pyotp) |
| CSRF | Flask-WTF — token sent as `X-CSRFToken` header |
| Task Queue | Celery 5 + Redis broker/backend |
| Scheduling | flask-crontab (minute-level cron jobs in Flask process) |
| Database | PostgreSQL 14 (prod) / SQLite in-memory (tests) |
| Migrations | Alembic via Flask-Migrate (`flask db upgrade`) |
| Rate Limiting | Flask-Limiter + Redis |
| File Processing | Pillow (images) + ffmpeg-python (video/GIF) |
| Content Import | gallery-dl (900+ sites) |
| Frontend | Vue 3 + Vite, Vue Router, Pinia, Axios |
| Server (prod) | Gunicorn |

---

## Backend Structure

### `Onani/routes/`

- `__init__.py` — registers all blueprints, sets up Flask-Login, CSRF, rate limiter
- `spa.py` — catch-all route that serves the Vue SPA at `/`
- `api/` → `api/v1/` — Flask-RESTful resources mounted at `/api/v1/`:
  - `auth.py` — Login, logout, register, CSRF token, OTP verification
  - `posts.py` — GET posts (paginated + tag filtering), POST vote/upload
  - `collections.py` — CRUD collections, add/remove posts
  - `comments.py` — GET/POST/DELETE comments on posts
  - `tags.py` — GET tags (sortable), PUT tag edits
  - `news.py` — GET news posts
  - `profile.py` — GET/PUT user profile, avatar upload
  - `users.py` — GET users list and a user's posts
  - `importer.py` — GET import task status, POST import URL
  - `index.py` — API root info (version, current user, IP)
  - `_admin/` — admin-only endpoints (ban, unban, stats, news management)

### `Onani/models/`

**User:**
- `_user.py` — `User` model: id, username, email, password_hash (argon2), nickname, role (enum), permissions (IntFlag), api_key, otp_token, created_at. Methods: `check_password()`, `check_otp()`, `has_permissions()`, `has_role()`.
- `ban.py` — `Ban`: user FK, since, expires, reason, posts_hidden, posts_deleted. Property `has_expired`.
- `roles.py` — `UserRoles` enum: MEMBER(0), ARTIST(1), PREMIUM(2), HELPER(100), MODERATOR(200), ADMIN(300), OWNER(666).
- `permissions.py` — `UserPermissions` IntFlag bitmask. Presets: DEFAULT, TRUSTED, MODERATION, ADMINISTRATION.
- `settings.py` — `UserSettings`: biography, avatar, custom_css, profile_colour, sfw_mode, encrypted_cookies, social links (DeviantArt, Discord, GitHub, Patreon, PayPal, Pixiv, Twitter).

**Post:**
- `_post.py` — `Post`: id, uploaded_at, status (enum), rating (enum), source (URL), description, uploader_id FK, hidden, water_count. M2M: tags, upvoters, downvoters, waters.
- `comment.py` — `PostComment`: post_id FK, user_id FK, content, locked, created_at.
- `rating.py` — `PostRating` enum: GENERAL("g"), QUESTIONABLE("q"), EXPLICIT("e").
- `status.py` — `PostStatus` enum: PENDING(0), APPROVED(1), DELETED(2), FLAGGED(3).

**Tag:**
- `_tag.py` — `Tag`: id, name (unique), type (enum), description, explicit (auto-marks posts explicit), restricted (premium-only), alias_of (self-ref FK), post_count, url, user_id (artist). Property `is_alias`.
- `type.py` — `TagType` enum: GENERAL, CHARACTER, ARTIST, SERIES, META, BANNED.

**Other:**
- `collection/collection_.py` — `Collection`: title, description, status (enum), created_at, creator FK. M2M posts via `collection_posts`.
- `collection/status.py` — `CollectionStatus`: PENDING, ACCEPTED, REJECTED.
- `news/_news.py` — `NewsPost`: author_id FK, title, content (HTML-escaped), type (enum), created_at.
- `news/type.py` — `NewsType`: ANNOUNCEMENT, PATCH_NOTES, MAINTENANCE.
- `error/error_.py` — `Error`: timestamp, exception_type, message, traceback, request_path, request_method. Used to log unhandled 500s.

**Schemas** (`Onani/models/schemas/`) — Marshmallow serialisers for all models: `user.py`, `post.py`, `tag.py`, `collection.py`, `news.py`, `comment.py`, `ban.py`.

### `Onani/services/`

Pure business logic — no Flask globals, raises typed exceptions:

- `auth.py` — `verify_credentials(user, password, otp)` → raises `InvalidCredentialsError`, `BannedError`, `DeletedAccountError`
- `users.py` — `create_user(username, password, email, role)` — generates api_key, otp_token, login_id; creates UserSettings
- `bans.py` — `create_ban(actor, user_id, expires, reason, delete_posts, hide_posts)` with role hierarchy checks; `delete_ban(user)`
- `posts.py` — `create_post()`, `upload_post()`, `parse_tags()`, `set_tags()`, `create_comment()`, video format detection, GIF conversion
- `files.py` — `create_avatar()`, `get_file_data()`, `determine_meta_tags()`, ffmpeg-based video processing
- `queries.py` — `query_posts(tags, exclude_tags, show_hidden, show_removed)` — tag filtering, deduplication, ordering
- `news.py` — `create_news(title, content, type, author)`
- `default.py` — `create_default_tags(filename)` bulk loader from JSON
- `errors.py` — `log_error(exception)` stores 500s in the Error table

### `Onani/controllers/`

Route decorators and helpers:

- `permissions.py` — `@permissions_required(UserPermissions.X)` — checks `current_user.has_permissions(flag)`
- `role.py` — `@role_required(UserRoles.X)` — checks `current_user.role.value >= required.value`
- `utils.py` — `is_url()`, `natural_join()`, misc helpers
- `crypto.py` — password/OTP hashing utilities
- `database/` — DB transaction helpers
- `exceptions/` — custom exception types

### `Onani/importers/`

Content import via gallery-dl:

- `gallery_dl_importer.py` — detects 900+ sites, extracts metadata/URLs without writing to disk. Maps site ratings → GENERAL/QUESTIONABLE/EXPLICIT.
- `_importedpost.py` — intermediate representation of an imported post
- `_utils.py` — shared utilities
- Per-site credentials via `GALLERY_DL_CONFIG_FILE` env var (standard gallery-dl config.json)

### `Onani/tasks/`

Celery async tasks (remember: **restart the celery container after editing**):

- `importer.py` — `import_post(post_url, importer_id, cookies_content)` — fetches & saves imported posts, reports progress via `self.update_state()`, cleans up DB session on error
- `database.py` — `database_test(user_id)`, `delete_user_posts(user_id)`
- `video.py` — placeholder video task

### Media and thumbnails

- Original media files are stored on disk using sharded paths (`<root>/<first-two-chars>/<filename>`).
- Thumbnails and sample images are generated/served by Flask routes and cached on disk.
- nginx image_filter is not required for thumbnail generation.

### `Onani/cron/`

- `tasks.py` — `remove_expired_bans()` scheduled every minute via `@crontab.job(minute="*/1")`. Queries Ban rows with `has_expired == True` and calls `delete_ban()`.

---

## Database Schema (Key Tables)

| Table | Key Columns |
|-------|-------------|
| `users` | id, username, email, password_hash, nickname, role, permissions, api_key, otp_token, created_at |
| `bans` | id, user FK, since, expires, reason, posts_hidden, posts_deleted |
| `settings` | id, user FK, biography, avatar, custom_css, profile_colour, sfw_mode, social connections |
| `posts` | id, uploaded_at, status, rating, source, description, uploader_id FK, hidden, water_count |
| `post_comments` | id, post_id FK, user_id FK, content, locked, created_at |
| `post_upvotes` | post_id FK, user_id FK |
| `post_downvotes` | post_id FK, user_id FK |
| `post_waters` | post_id FK, user_id FK |
| `post_tags` | post_id FK, tag_id FK |
| `tags` | id, name (unique), type, description, explicit, restricted, alias_of FK, post_count, url, user_id FK |
| `collections` | id, title, description, status, created_at, creator FK |
| `collection_posts` | collection_id FK, post_id FK |
| `news` | id, author_id FK, created_at, title, content, type |
| `errors` | id, timestamp, exception_type, message, traceback, request_path, request_method |
| `tag_blacklist` | user_id FK, tag_id FK |

Migrations live in `migrations/versions/`. Always generate new migrations with `flask db migrate` and apply with `flask db upgrade`.

---

## Auth & Permissions

**Login:** session cookie (Flask-Login, 7-day duration). API key auth also supported via `Authorization: <key>` header.

**Password:** Argon2 hashing. Optional TOTP 2FA — secret stored in `User.otp_token`, verified with pyotp.

**Roles** (numeric, compared with `>=`): MEMBER → ARTIST → PREMIUM → HELPER → MODERATOR → ADMIN → OWNER.

**Permissions** (IntFlag bitmask on `User.permissions`). Granular flags cover: posts, tags, collections, comments, flags/reports, news, users, site-wide. Presets:
- `DEFAULT` — create posts/comments/collections, flag
- `TRUSTED` — + create tags, import, priority flag
- `MODERATION` — + edit/merge/delete content and comments
- `ADMINISTRATION` — + delete/ban/manage users, news, bypass rate limits, view logs

**Bans:** stored as a `Ban` row linked to the user. Checked in the route loader — banned users are treated as unauthenticated. Expired bans are auto-removed by the cron job.

---

## Frontend Structure (`frontend/src/`)

- `main.js` — creates Vue app, mounts Pinia + Router
- `router/index.js` — Vue Router; `beforeEach` guard redirects unauthenticated users to `/login`
- `stores/auth.js` — Pinia store: `user`, `isAuthenticated`, `fetchUser()`, `login()`, `logout()`
- `api/client.js` — Axios instance (`baseURL: /api/v1`, `withCredentials: true`); request interceptor auto-attaches `X-CSRFToken` on mutations
- `layouts/DefaultLayout.vue` — main shell (header/nav/footer)
- `composables/useSfwMode.js` — reactive SFW mode toggle
- `components/Pagination.vue` — reusable pagination
- `views/` — 18 route-level components: HomeView, PostsView, PostView, TagsView, TagView, UsersView, UserView, NewsView, ArticleView, CollectionsView, CollectionView, UploadView, ImportView, ProfileView, AdminView, LoginView, RegisterView, NotFoundView
