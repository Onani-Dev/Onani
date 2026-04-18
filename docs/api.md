# API Reference

All REST API endpoints are served under the `/api/v1/` prefix.

## Base URL

```
http://localhost:8080/api/v1      # production (nginx)
http://localhost:5000/api/v1      # development (Flask direct)
```

## Authentication

Authentication uses **Flask-Login session cookies** set on login. Session cookies are `HttpOnly` and `SameSite=Lax`.

**CSRF protection:** All mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`) must include a `X-CSRFToken` header. Retrieve a token from [`GET /auth/csrf`](#get-authcsrf).

**Error format** (all 4xx/5xx responses):

```json
{ "message": "Human-readable error description." }
```

## Pagination

Paginated list endpoints return:

```json
{
  "data": [...],
  "total": 1234,
  "next_page": 2,
  "prev_page": null
}
```

`next_page` / `prev_page` are `null` when there is no next/previous page.

---

## Auth

### POST /auth/login

Log in with username and password.

Rate limited: **10 requests/minute**.

**Request body** (JSON):

| Field      | Type    | Required | Description              |
| ---------- | ------- | -------- | ------------------------ |
| `username` | string  | Yes      | Account username         |
| `password` | string  | Yes      | Account password         |
| `otp`      | integer | No       | TOTP code (if 2FA is on) |

**Responses:**

| Code | Body                                                         |
| ---- | ------------------------------------------------------------ |
| 200  | [User object](#user-object) + sets `current_user_id` cookie  |
| 401  | `{ "message": "Invalid username or password." }`            |
| 403  | `{ "message": "..." }` — banned or deleted account          |

---

### POST /auth/logout

Log out the current session. Requires authentication.

**Responses:**

| Code | Body                                          |
| ---- | --------------------------------------------- |
| 200  | `{ "message": "Successfully logged out." }`   |
| 401  | Not authenticated                             |

---

### POST /auth/register

Create a new account.

Rate limited: **10 requests/hour**.

**Request body** (JSON):

| Field      | Type   | Required | Description             |
| ---------- | ------ | -------- | ----------------------- |
| `username` | string | Yes      | Desired username        |
| `password` | string | Yes      | Account password        |
| `email`    | string | No       | Optional email address  |

**Responses:**

| Code | Body                                                         |
| ---- | ------------------------------------------------------------ |
| 201  | [User object](#user-object) + sets `current_user_id` cookie  |
| 400  | Validation error                                             |
| 409  | `{ "message": "Username is already taken." }`               |

---

### GET /auth/me

Return authentication status and the current user object if logged in.

**Responses:**

| Code | Body                                                               |
| ---- | ------------------------------------------------------------------ |
| 200  | `{ "authenticated": true, ...`[User fields](#user-object)`... }`  |
| 401  | `{ "authenticated": false }`                                       |

---

### GET /auth/csrf

Return a fresh CSRF token. Call this once on SPA load and store the result in a header interceptor.

**Response (200):**

```json
{ "csrf_token": "<token>" }
```

---

## Posts

### GET /posts

List posts. Supports tag filtering.

**Query parameters:**

| Name       | Type    | Default | Description                                             |
| ---------- | ------- | ------- | ------------------------------------------------------- |
| `page`     | integer | 1       | Page number                                             |
| `per_page` | integer | config  | Results per page (capped at `API_MAX_PER_PAGE`)         |
| `tags`     | string  | —       | Space-separated tag query; prefix `-` to exclude a tag  |

**Response (200):** Paginated [Post objects](#post-object).

---

### GET /post

Retrieve a single post by ID.

**Query parameters:**

| Name | Type    | Required | Description |
| ---- | ------- | -------- | ----------- |
| `id` | integer | Yes      | Post ID     |

**Response (200):** [Post object](#post-object) with additional `has_upvoted` and `has_downvoted` booleans.

**Response (404):** Post not found.

---

### PUT /post · PATCH /post

Edit a post. Requires authentication; editors must have permission to edit (own post or moderator).

**Request body** (JSON):

| Field         | Type   | Description                          |
| ------------- | ------ | ------------------------------------ |
| `id`          | int    | **Required.** Post ID                |
| `tags`        | string | Space-separated list of new tags     |
| `old_tags`    | string | Previous tag string (diff-based)     |
| `rating`      | string | `"s"` / `"q"` / `"e"`               |
| `source`      | string | Source URL                           |
| `description` | string | Post description text                |

**Response (200):** Updated [Post object](#post-object).

---

### POST /posts/upload

Upload a new post. Requires authentication. Content-Type must be `multipart/form-data`.

Rate limited: **10 requests/minute**.

**Form fields:**

| Field         | Type   | Required | Description                      |
| ------------- | ------ | -------- | -------------------------------- |
| `file`        | file   | Yes      | Image or video file              |
| `tags`        | string | Yes      | Space-separated tag list         |
| `rating`      | string | Yes      | `"s"` / `"q"` / `"e"`           |
| `source`      | string | No       | Source URL                       |
| `description` | string | No       | Post description                 |

**Responses:**

| Code | Body                                  |
| ---- | ------------------------------------- |
| 201  | [Post object](#post-object)           |
| 400  | Validation error or unreadable file   |
| 401  | Not authenticated                     |

---

### POST /posts/vote

Vote on a post. Toggles — sending the same vote type again removes the vote.

Requires authentication.

**Request body** (JSON):

| Field     | Type   | Required | Description                |
| --------- | ------ | -------- | -------------------------- |
| `post_id` | int    | Yes      | Post ID                    |
| `type`    | string | Yes      | `"upvote"` or `"downvote"` |

**Response (200):**

```json
{ "score": 12, "has_upvoted": true, "has_downvoted": false }
```

---

### POST /posts/water

Increment a post's water count. Requires authentication.

**Request body** (JSON): `{ "post_id": 1 }`

**Response (200):** `{ "water_count": 5 }`

---

### GET /posts/home

Return curated data for the home page.

**Response (200):**

```json
{
  "recent":  [ ...PostObject... ],
  "popular": [ ...PostObject... ],
  "random":  PostObject | null,
  "tags":    [ ...TagObject... ]
}
```

---

## Comments

### GET /comments

List comments for a post.

**Query parameters:**

| Name       | Type    | Required | Description                              |
| ---------- | ------- | -------- | ---------------------------------------- |
| `post_id`  | integer | Yes      | Post ID                                  |
| `page`     | integer | No       | Page number                              |
| `per_page` | integer | No       | Results per page (capped by server)      |

**Response (200):** Paginated list, keys `data`, `next`, `prev`, `total`.

---

### POST /comments

Create a comment. Requires authentication and `CREATE_COMMENTS` permission.

Rate limited: **5 requests/minute**.

**Request body** (JSON):

| Field     | Type   | Required | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `post_id` | int    | Yes      | ID of the post to comment on  |
| `content` | string | Yes      | Content (1–2000 characters)   |

**Response (200):** Comment object.

---

### DELETE /comments

Delete a comment. Requires `DELETE_COMMENTS` permission.

**Request body** (JSON): `{ "comment_id": 42 }`

**Response (200):** `{ "message": "Comment deleted." }`

---

## Tags

### GET /tags

List or retrieve tags.

**Query parameters:**

| Name        | Type    | Description                                                     |
| ----------- | ------- | --------------------------------------------------------------- |
| `id`        | integer | If provided, returns a single tag                               |
| `page`      | integer | Page number (default 0)                                         |
| `per_page`  | integer | Results per page                                                |
| `sort`      | string  | `id` / `name` / `type` / `post_count`                          |
| `order`     | string  | `asc` / `desc` (default `desc`)                                 |
| `min_posts` | integer | Filter tags with at least this many posts                       |

**Response (200):** Single [Tag object](#tag-object) when `id` is set, otherwise paginated list.

---

### PUT /tags

Rename or retype a tag. Requires moderator role.

**Request body** (JSON):

| Field  | Type   | Required | Description                                                          |
| ------ | ------ | -------- | -------------------------------------------------------------------- |
| `id`   | int    | Yes      | Tag ID                                                               |
| `name` | string | No       | New tag name (lowercased, spaces → underscores)                      |
| `type` | string | No       | `general` / `artist` / `character` / `copyright` / `meta` / `banned`|

**Response (200):** Updated [Tag object](#tag-object).

**Response (409):** `{ "message": "Tag name already exists." }`

---

### GET /tags/autocomplete

Tag name prefix search for the post editor.

**Query parameters:**

| Name    | Type   | Required | Description              |
| ------- | ------ | -------- | ------------------------ |
| `query` | string | Yes      | Prefix to search for     |

**Response (200):** `{ "data": [ ...TagObject... ] }`

---

## Collections

### GET /collections

List collections or retrieve one by ID.

**Query parameters:**

| Name       | Type    | Description                                   |
| ---------- | ------- | --------------------------------------------- |
| `id`       | integer | If set, returns a single collection with posts |
| `page`     | integer | Page number (default 1)                        |
| `per_page` | integer | Results per page                               |

**Response (200):** Single [Collection object](#collection-object) or paginated list (posts excluded in list).

---

### POST /collections

Create a collection. Requires authentication.

**Request body** (JSON):

| Field         | Type   | Required | Description             |
| ------------- | ------ | -------- | ----------------------- |
| `title`       | string | Yes      | Collection title        |
| `description` | string | No       | Description text        |

**Response (201):** [Collection object](#collection-object).

---

### PUT /collections

Update a collection's title or description. Requires authentication and ownership or moderator role.

**Request body** (JSON):

| Field         | Type   | Required | Description              |
| ------------- | ------ | -------- | ------------------------ |
| `id`          | int    | Yes      | Collection ID            |
| `title`       | string | No       | New title                |
| `description` | string | No       | New description          |

**Response (200):** Updated [Collection object](#collection-object).

**Response (403):** Not the owner and not a moderator.

---

### DELETE /collections

Delete a collection. Requires authentication and ownership or moderator role.

**Request body** (JSON): `{ "id": 1 }`

**Response (204):** Empty body.

**Response (403):** Not the owner and not a moderator.

---

### POST /collections/posts

Add a post to a collection. Requires ownership or moderator role.

**Request body** (JSON):

| Field           | Type | Required |
| --------------- | ---- | -------- |
| `collection_id` | int  | Yes      |
| `post_id`       | int  | Yes      |

**Response (200):** Updated [Collection object](#collection-object) including posts.

---

### DELETE /collections/posts

Remove a post from a collection. Requires ownership or moderator role.

**Request body** (JSON): `{ "collection_id": 1, "post_id": 5 }`

**Response (200):** Updated [Collection object](#collection-object).

---

## News

### GET /news

List published news articles.

**Response (200):** `{ "data": [ ...NewsObject... ] }`

---

## Users

### GET /users

List users or retrieve a single user. Requires authentication.

**Query parameters:**

| Name       | Type    | Description                        |
| ---------- | ------- | ---------------------------------- |
| `id`       | integer | If set, returns a single user      |
| `page`     | integer | Page number (default 1)            |
| `per_page` | integer | Results per page                   |

**Response (200):** Single [User object](#user-object) or paginated list.

---

### GET /users/posts

List posts uploaded by a user. Public, no authentication required.

**Query parameters:**

| Name       | Type    | Required | Description    |
| ---------- | ------- | -------- | -------------- |
| `user_id`  | integer | Yes      | User ID        |
| `page`     | integer | No       |                |
| `per_page` | integer | No       |                |

**Response (200):** Paginated [Post objects](#post-object).

---

## Profile

### GET /profile

Return the authenticated user's full profile. Requires authentication.

**Response (200):** [User object](#user-object).

---

### PUT /profile · PATCH /profile

Update the authenticated user's account or profile settings. Requires authentication. All fields are optional.

**Request body** (JSON):

| Field             | Type    | Description                                         |
| ----------------- | ------- | --------------------------------------------------- |
| `nickname`        | string  | Display name (empty string clears it)               |
| `email`           | string  | New email — requires `current_password`             |
| `new_password`    | string  | New password — requires `current_password`          |
| `current_password`| string  | Current password (needed for email/password change) |
| `biography`       | string  | Profile bio text                                    |
| `profile_colour`  | string  | CSS colour string                                   |
| `sfw_mode`        | boolean | Toggle SFW (blur explicit content)                  |
| `otp_enabled`     | boolean | Enable/disable 2FA                                  |
| `profile_picture` | string  | Base64-encoded image data for avatar                |

**Response (200):** Updated [User object](#user-object).

---

### GET /profile/cookies

Check whether the user has an encrypted cookies file stored.

**Response (200):** `{ "has_cookies": true }`

---

### POST /profile/cookies

Upload and encrypt a gallery-dl cookies file. Requires authentication. Content-Type `multipart/form-data`.

| Field      | Description                              |
| ---------- | ---------------------------------------- |
| `cookies`  | Cookie file (max 512 KB)                 |
| `password` | Current account password (for encryption)|

**Response (200):** `{ "message": "Cookies saved." }`

---

### DELETE /profile/cookies

Remove the stored cookies file. Requires authentication.

**Response (200):** `{ "message": "Cookies removed." }`

---

### GET /profile/otp

Return 2FA status and a TOTP QR code for setup.

**Response (200):**

```json
{
  "enabled": false,
  "uri": "otpauth://totp/...",
  "qr_code": "data:image/png;base64,..."
}
```

---

### POST /profile/otp

Verify a TOTP code and enable 2FA.

**Request body** (JSON): `{ "code": 123456 }`

**Response (200):** `{ "enabled": true }` · **400:** invalid code.

---

### DELETE /profile/otp

Disable 2FA.

**Response (200):** `{ "enabled": false }`

---

## Importer

### POST /import

Queue a post import from an external URL. Requires authentication.

**Request body** (JSON):

| Field | Type   | Required | Description          |
| ----- | ------ | -------- | -------------------- |
| `url` | string | Yes      | URL to import from   |

**Response (200):** `{ "id": "<celery-task-id>" }`

---

### GET /import

Poll the status of an import task.

**Query parameters:**

| Name | Type   | Required | Description      |
| ---- | ------ | -------- | ---------------- |
| `id` | string | Yes      | Celery task ID   |

**Response (200):**

```json
{
  "status": "PENDING | PROGRESS | SUCCESS | FAILURE",
  "result": { ... } | null,
  "meta":   { "current": 1, "total": 10 } | null
}
```

---

## Admin

All admin endpoints require authentication. Role requirements are noted per endpoint.

---

### GET /admin/stats

Return site-wide counts. Requires **moderator** role.

**Response (200):**

```json
{ "posts": 42, "users": 10, "tags": 800, "collections": 5, "errors": 0 }
```

---

### GET /admin/errors

List logged application errors. Requires `VIEW_LOGS` permission.

**Query parameters:** `page`, `per_page` (default 20).

**Response (200):**

```json
{
  "data": [{ "id": "uuid", "exception_type": "ValueError", "created_at": "2024-01-01T00:00:00" }],
  "total": 3, "page": 1, "next_page": null, "prev_page": null
}
```

---

### GET /admin/celery-logs

Tail the Celery worker log file. Requires **moderator** role.

**Query parameters:**

| Name    | Type    | Default | Description              |
| ------- | ------- | ------- | ------------------------ |
| `lines` | integer | 100     | Number of tail lines (max 500) |

**Response (200):**

```json
{ "lines": ["[2024-01-01 00:00:00: INFO] ..."], "available": true }
```

When the log file has not been created yet:

```json
{ "lines": [], "available": false }
```

---

### POST /admin/tasks

Run a background administrative task. Requires **admin** role.

**Request body** (JSON):

| Field  | Type   | Required | Choices                                                           |
| ------ | ------ | -------- | ----------------------------------------------------------------- |
| `task` | string | Yes      | `remove_expired_bans` · `backfill_video_thumbnails` · `recount_tags` |

**Response (200):** `{ "message": "Task queued." }`

---

### GET /admin/users

List users (admin view with additional fields). Requires **moderator** role.

**Query parameters:** `page`, `per_page`, `id`.

---

### GET /admin/imports

List active import tasks running on Celery workers. Requires **moderator** role.

**Response (200):**

```json
{
  "tasks": [{ "id": "task-uuid", "url": "https://...", "worker": "celery@hostname" }]
}
```

---

### POST /admin/ban _(legacy)_

Ban a user. Requires **admin** role.

**Request body** (JSON): `{ "expires": "<ISO datetime>", "reason": "..." }`

---

### POST /admin/news _(legacy)_

Create a news article. Requires **admin** role.

**Request body** (JSON): `{ "title": "...", "content": "..." }`

---

## Object Schemas

### Post object

```json
{
  "id": 1,
  "file_url": "/static/images/abc.jpg",
  "sample_url": "/static/images/thumb_abc.jpg",
  "file_type": "jpg",
  "width": 1920,
  "height": 1080,
  "file_size": 204800,
  "rating": "s",
  "score": 3,
  "source": "https://example.com/post/1",
  "description": "",
  "created_at": "2024-01-01T00:00:00",
  "uploader": 7,
  "tags": [ ...TagObject... ]
}
```

`rating` values: `s` (safe) · `q` (questionable) · `e` (explicit).

---

### Tag object

```json
{
  "id": 42,
  "name": "blue_eyes",
  "type": "general",
  "post_count": 123
}
```

`type` values: `general` · `artist` · `character` · `copyright` · `meta` · `banned`.

---

### User object

```json
{
  "id": 5,
  "username": "alice",
  "nickname": "Alice",
  "role": "user",
  "post_count": 10,
  "avatar_url": "/static/avatars/alice.jpg",
  "biography": "...",
  "profile_colour": "#ff6699",
  "created_at": "2024-01-01T00:00:00"
}
```

---

### Collection object

```json
{
  "id": 3,
  "title": "My Favourites",
  "description": "A personal collection.",
  "creator": 5,
  "status": "accepted",
  "created_at": "2024-01-01T00:00:00",
  "posts": [ ...PostObject... ]
}
```

`posts` is omitted in list responses and included in single-collection responses.
