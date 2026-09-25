# Backend correctness / quality audit

Scope: `onani/models/**`, `onani/controllers/database/**`, `onani/tasks/**`,
`onani/cron/**`, `migrations/**`, `run.py`, `celery_worker.py`, `tests/`.
Read-only audit; authz/injection out of scope (covered elsewhere).

## pytest baseline

**Could not run.** No virtualenv is present in the repo and the system
Python (`C:\Users\kapsikkum\AppData\Local\Programs\Python\Python313\python.exe`)
has no packages installed (`ModuleNotFoundError: No module named pytest`).
`requirements-dev.txt` and `requirements.txt` (which pulls in TensorFlow via
`requirements-ml.txt` for the DeepDanbooru path) were not installed, since
doing so is a heavyweight, non-read-only action outside this audit's remit.
No baseline pytest result is available — set up a venv and install
`requirements*.txt` to get one.

## Summary

The recent stop-scan feature (commit `2c81ce6`) has a real, unfixed
TOCTOU race between the DELETE (stop) endpoint and the scan task's own
finalize code: stopping a scan does not reliably keep it stopped, because
both write `last_scan_status`/`last_scan_task_id` on the same row with no
locking or fencing token. A second concurrency bug in the same file lets
two POST requests both pass the "already running" check and start
duplicate scans. Separately, roughly 600 lines of `onani/controllers/database/`
(`posts.py`, `bans.py`, `users.py`, `news.py`, `queries.py`) are dead code
that only `tests/test_controllers.py` still exercises — the app's real code
paths in `onani/services/` are consequently under-tested by that suite.

**Findings by severity:** High: 2, Medium: 4, Low: 3.

## Findings

### H1 — Stop-scan race: a stopped scan can silently resurrect itself
- **File:** `onani/routes/api/v1/libraries.py:316-344` (`LibraryScan.delete`) and
  `onani/tasks/library.py:394-407` (finalize block)
- **Problem:** `DELETE /libraries/<id>/scan` revokes the Celery task, then
  unconditionally sets `last_scan_status = "IDLE"` and `last_scan_task_id = None`
  and commits — without any row lock or check that the task has actually
  stopped. `scan_library`'s own finalize code (`library.py:397-407`) writes
  `last_scan_status` (`SUCCESS`/`FAILED`/`PARTIAL`) and
  `last_scan_task_id = self.request.id` from inside the worker process with
  no awareness of `revoke()`/IDLE reset. If `revoke(terminate=True)` doesn't
  land before the task reaches its next commit point (e.g. it is between the
  per-file `try` block and the finalize block, or `terminate` is delivered
  but caught by a `try/except Exception` inside the per-file loop and the
  loop simply continues to the next file), the task's later commit
  overwrites the just-issued IDLE reset — the library silently goes back to
  "SCANNING"/"SUCCESS" and the stale `last_scan_task_id` reappears, exactly
  the failure mode a "stop" button should prevent. There is no fencing
  token (e.g. compare-and-swap on `last_scan_task_id`, or checking Celery
  `REVOKED` state) to make the writes idempotent/ordered.
- **Fix:** Use an optimistic fencing check: only let the task's finalize
  block (and every mid-loop commit of `last_scan_status`) write if
  `ExternalLibrary.last_scan_task_id == self.request.id` still matches
  (`UPDATE ... WHERE id=:id AND last_scan_task_id=:task_id`), and have the
  task periodically check `self.is_aborted()`/re-read its own DB row for a
  "stop requested" flag rather than relying solely on `SIGTERM` timing.
- **Effort:** M

### H2 — Duplicate-scan race: two POST requests can both start a scan
- **File:** `onani/routes/api/v1/libraries.py:290-314` (`LibraryScan.post`)
- **Problem:** The "already running" guard is check-then-act with no
  row lock: `lib.last_scan_status == "SCANNING"` is read, `_task_is_active()`
  makes an out-of-band Celery broker call, and only then is the new
  `task_id`/`SCANNING` status written and committed. Two concurrent POSTs
  (e.g. a double-click, or the frontend retrying) can both read
  "not currently active" and both pass, each writing its own `task_id` and
  dispatching `scan_library.apply_async`. Two scanner tasks then run over
  the same directory concurrently. The `uq_library_file_path` unique
  constraint (`onani/models/external_library.py:155-157`) limits the damage
  to `IntegrityError`s that get caught by the per-file `except Exception`
  in `library.py:300-321` and marked `FAILED` (so no data corruption), but
  the scan still does 2x the I/O/hashing work and pollutes
  `ExternalLibraryFile.error` with spurious `IntegrityError` noise, and
  whichever task commits its finalize block last wins the final
  status/task_id, which may not be the task the caller thinks is "the"
  scan.
- **Fix:** Take a `SELECT ... FOR UPDATE` on the library row (or a
  `UPDATE external_libraries SET last_scan_status='SCANNING', last_scan_task_id=:tid WHERE id=:id AND (last_scan_status IS NULL OR last_scan_status != 'SCANNING' OR NOT <active>)`
  single-statement compare-and-swap) instead of read-then-write.
- **Effort:** S–M

### M1 — `onani/controllers/database/{posts,bans,users,news,queries}.py` are dead code, and the test suite covers the dead copies instead of the real code
- **Files:** `onani/controllers/database/posts.py` (291 lines),
  `bans.py` (88), `users.py` (20), `news.py` (28), `queries.py` (36),
  `default.py` (36) — ~500 lines total. `tests/test_controllers.py`
- **Problem:** `onani/controllers/database/__init__.py:3-18` re-exports
  `create_avatar, create_ban, create_comment, ..., create_post, ...,
  set_tags, upload_post` **directly from `onani.services`**, explicitly
  labelled "Backward-compatibility shim — all logic now lives in
  onani/services/". That means the sibling files in the same directory
  (`posts.py`, `bans.py`, `users.py`, `news.py`, `queries.py`) that define
  their *own* `create_post`, `create_ban`, `create_user`,
  `create_news`, `query_posts` are never reached through the package's
  public API — confirmed via `grep`, nothing outside this directory
  imports `onani.controllers.database.posts` or `.bans` or `.users` or
  `.news` or `.queries` by submodule path, and `onani/__init__.py` only
  reaches into `controllers.database.errors` directly (not into these
  files). However, `tests/test_controllers.py` imports these dead
  submodules directly (e.g. `from onani.controllers.database.users import
  create_user`, `from onani.controllers.database.posts import
  create_comment`, `from onani.controllers.database.bans import
  create_ban/delete_ban`), so the whole file is testing logic the running
  application never executes. The real implementations
  (`onani/services/posts.py::create_post/set_tags/parse_tags`,
  `services/*::create_ban`, etc.) that back the actual routes and the
  `scan_library`/importer Celery tasks have **no direct unit tests** of
  their own — this is the actual coverage gap.
  A concrete consequence of the drift: the dead
  `controllers/database/posts.py::create_post` (unlike
  `services/posts.py::create_post`) has **no pre-flight/IntegrityError
  duplicate check** on `sha256_hash`/`filename`, and it writes the image
  file to disk (`open(filepath, "wb")`, line 211-213) *before*
  `db.session.commit()` with no cleanup on failure — a duplicate upload
  hitting that code path would leave an orphaned file on disk and crash
  with an unhandled `IntegrityError`. It happens not to matter today only
  because nothing calls it.
- **Fix:** Delete `posts.py`, `bans.py`, `users.py`, `news.py`,
  `queries.py`, `default.py` from `onani/controllers/database/` (keep
  `errors.py`, which is genuinely used, and `__init__.py`'s shim). Rewrite
  `tests/test_controllers.py` to import from `onani.services` (or from the
  `onani.controllers.database` package root, which already re-exports the
  real functions) so it exercises the code that actually runs in
  production.
- **Effort:** M (mechanical deletion + retargeting one test file; verify no
  other stray references first)

### M2 — `_task_is_active` / DELETE endpoint disagree on what counts as "active", and DELETE's revoke check races the same way POST's does
- **File:** `onani/routes/api/v1/libraries.py:237-251` vs `:326-335`
- **Problem:** `_task_is_active()` (used by `POST`) only treats
  `STARTED`/`PROGRESS` as active — it explicitly does *not* treat a bare
  `PENDING` state as active (comment: "worker crashed" case). `DELETE`,
  however, revokes and reports `revoked=True` for `PENDING` too
  (`task.state in ("PENDING", "STARTED", "PROGRESS")`, line 331). This
  means: (a) if a task is genuinely queued-but-not-yet-started (a true
  `PENDING`, e.g. worker pool momentarily saturated with
  `--concurrency=10` and 11 scans requested), `POST` would treat it as
  inactive and let a caller start a *second* scan for the same library
  before the first one even begins, doubling the race window in H2; and
  (b) `DELETE`'s "revoked" flag is misleading — it reports `True` for a
  task that may never have been dispatched to a worker at all (broker-side
  PENDING), so the admin UI shows "stopped a running scan" when nothing
  was actually running yet.
- **Fix:** Share one predicate between `POST` and `DELETE` (reuse
  `_task_is_active`, and additionally revoke on plain `PENDING` too since
  `revoke()` without `terminate` is safe/idempotent for not-yet-started
  tasks — it just removes them from the queue).
- **Effort:** S

### M3 — `create_post`/`set_tags` file-write-then-commit ordering has no cleanup on failure (services path)
- **File:** `onani/services/posts.py:259-286`
- **Problem:** The services `create_post` is safer than the dead
  controllers version (it does the duplicate pre-check +
  `begin_nested()`/flush before writing tags), but the final `open(filepath,
  "wb")` write (line 271-274) still happens *before* `db.session.commit()`
  (line 284). If `set_tags` (called at line 268, before the file write) or
  the final commit itself raises for any reason downstream of the file
  write (disk full, permissions, thumbnail generation
  `create_video_thumbnail` failing silently vs. loudly, or a later
  `IntegrityError` from a concurrent duplicate tag/post that the
  begin_nested savepoint didn't cover), the file already sits on disk with
  no corresponding DB row and no cleanup — an orphaned file. This is a
  smaller window than the dead controllers version (most of the failure
  modes are covered upstream), but it is not eliminated.
- **Fix:** Wrap the file write in a `try/except` that unlinks the file on
  any exception before re-raising, or write to a temp path and `os.replace`
  only after a successful commit.
- **Effort:** S

### M4 — `scan_library` reads the entire `ExternalLibraryFile` set into memory up front, and `generate_all_thumbnails`/`deepdanbooru` batch tasks load all `Post` rows at once
- **Files:** `onani/tasks/library.py:114-117` (`existing = {f.file_path: f for f in library.files.all()}`),
  `onani/tasks/thumbnails.py:41` (`Post.query.order_by(Post.id.asc()).all()`),
  `onani/tasks/deepdanbooru.py:28,32-37` (`Post.query...all()`)
- **Problem:** These are single queries (not N+1), but they materialize the
  full result set — and in `library.py` the full dict is rebuilt again after
  every per-file exception (`library.py:307-311`,
  `existing = {f.file_path: f for f in ExternalLibraryFile.query.filter_by(library_id=library_id).all()}`),
  which is an O(n) reload on every single failed file in a scan. For a
  library with hundreds of thousands of files (the size the code's own
  comments target — see `LibraryFileList`'s pagination comment,
  `libraries.py:226-228`) and a scan with many transient per-file failures,
  this becomes an O(n²)-ish pattern (full reload of all `ExternalLibraryFile`
  rows for that library on every failure) and unbounded memory growth for
  the thumbnail/deepdanbooru "all posts" tasks as the post count grows.
- **Fix:** For `library.py`, avoid rebuilding the whole `existing` dict on
  every per-file exception — only the just-failed file's row needs
  re-fetching (`ExternalLibraryFile.query.filter_by(library_id=library_id, file_path=path).first()`).
  For thumbnails/deepdanbooru, use `Post.query.order_by(Post.id.asc()).yield_per(500)`
  or a keyset-paginated loop instead of `.all()`.
- **Effort:** S–M

### L1 — `ExternalLibrary.last_scan_status` docstring is stale
- **File:** `onani/models/external_library.py:58`
- **Problem:** Comment says `# IDLE / SCANNING / SUCCESS / FAILED`; commit
  `2c81ce6` added a `PARTIAL` status (`library.py:400-405`) and the DELETE
  endpoint's `IDLE` reset. The column is a free-text `String(20)` with no
  CHECK constraint, so this is purely a documentation drift, but it's
  actively misleading for anyone reading the model to understand the state
  machine.
- **Fix:** Update the comment to list all five states, or add a CHECK
  constraint enumerating them.
- **Effort:** S

### L2 — `cron/tasks.py::remove_expired_bans` loop
- **File:** `onani/cron/tasks.py:12-22`
- **Problem:** Runs every minute, loads every non-permanent `Ban` row, and
  calls `delete_ban(ban.user)` in a Python loop for each expired one. Not a
  true N+1 (single initial query), but `delete_ban` (not audited here) is
  called once per expired ban with no batching; fine at current expected
  scale but worth flagging if ban volume grows.
- **Fix:** Low priority; batch-delete if this ever shows up in profiling.
- **Effort:** S

### L3 — `_task_is_active`/GET status endpoint swallow all Celery backend errors silently
- **File:** `onani/routes/api/v1/libraries.py:247-251, 268-279, 328-335`
- **Problem:** All three call sites wrap the Celery `AsyncResult` calls in
  bare `except Exception: pass`. A genuine broker/result-backend outage
  (e.g. Redis down) becomes indistinguishable from "task not active" —
  `POST` would then let scans start freely with no way to detect
  already-running ones, and `GET` would silently fall back to the
  possibly-stale DB `last_scan_status` with no indication to the client
  that the live status check failed.
- **Fix:** Log the exception (even at debug level) so an operator can
  correlate "why did two scans run" with a backend outage; consider
  surfacing a `"status_check_degraded": true` flag in the GET response.
- **Effort:** S

## Notes on things checked and found fine
- `uq_library_file_path` unique constraint (model `external_library.py:155-157`,
  migration `b2c3d4e5f6a7`) correctly bounds the damage from H2's duplicate
  scans — no silent data corruption, only wasted work + noisy `FAILED`
  entries.
- The commit `2c81ce6` diff shows the old post-scan
  `for tag in Tag.query.all(): tag.recount_posts()` loop was removed from
  `library.py`. This is **not** a regression: `services/posts.py::create_post`
  → `set_tags()` already calls `t.recount_posts()` for every added/removed
  tag per post at creation time, so the removed loop was redundant
  (unbounded `Tag.query.all()` N+1 over every tag in the whole system on
  every scan) — deleting it was a correct cleanup.
- Migration `f1a2b3c4d5e6` uses the Postgres-only `ctid` system column in a
  raw `DELETE ... WHERE ctid NOT IN (...)`. This looks non-portable at
  first glance, but the app only ever targets Postgres in production
  (`onani/config.py` default `DATABASE_URL`, `docker-compose.yml`); tests
  use SQLite but go through `db.create_all()`, not Alembic, so this
  migration is never exercised against SQLite. Not a bug.
- `_iter_scan_directory`'s hidden-file/dir skip (`library.py:32-56`,
  added in `2c81ce6`) correctly prunes `dirnames` in place for `os.walk`
  and checks `entry.name.startswith(".")` in the non-recursive branch — no
  bug found here.
- `onani/tasks/importer.py::_dispatch_next_queued` correctly uses
  `with_for_update(skip_locked=True)` for its own queue-draining race and
  rolls back to release the lock when no row is found — a good pattern
  that H1/H2 above should probably borrow.
