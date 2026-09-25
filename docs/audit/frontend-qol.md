# Frontend Quality/QoL Audit

Read-only audit of `frontend/src/**`, frontend config, `README.md`, `docs/`, `onani.toml.example`.
Date: 2026-09-25. Only findings verified by reading the actual source are listed.

---

## High

### H1 — Unsanitized HTML rendered via `v-html`
- **File**: `frontend/src/views/ArticleView.vue:5`
- **Problem**: `<div v-html="article.content"></div>` renders `article.content` (from `GET /news`) as raw HTML with no sanitization (no DOMPurify or similar). If news/article content can ever be authored by anyone other than a fully trusted admin (or if the admin account is compromised), this is a stored-XSS vector. Even for admin-only content, defense in depth is cheap here.
- **Fix**: Sanitize with a library (e.g. `dompurify`) before binding: `v-html="sanitize(article.content)"`, or render as Markdown into safe nodes instead of raw HTML.
- **Effort**: S

---

## Medium

### M1 — Seven views fetch data with no error handling (no catch, no error UI)
- **Files**:
  - `frontend/src/views/ArticleView.vue:17-19` (`onMounted` → `api.get('/news', ...)`, no try/catch)
  - `frontend/src/views/FavouritesView.vue:37-46` (`fetchFavourites` sets `loading` but never catches a failed request — a rejected promise leaves `loading` stuck `true` forever)
  - `frontend/src/views/HomeView.vue:69-71` (no try/catch around `api.get('/posts/home')`)
  - `frontend/src/views/NewsView.vue:21-25` (no try/catch)
  - `frontend/src/views/TagsView.vue:41-45` (no try/catch)
  - `frontend/src/views/UserView.vue:33-40` (two awaited `api.get` calls, no try/catch)
  - `frontend/src/views/UsersView.vue:26-30` (no try/catch)
- **Problem**: On a network error or non-2xx response, these views throw inside an async function with nowhere to catch it. The page is left in an indefinite loading/blank state (in `FavouritesView`, `loading.value = false` is inside the `try` body's `finally`-equivalent tail — actually never reached on error since there's no `finally`) with no user-facing error message and no retry affordance.
- **Fix**: Wrap fetches in try/catch, set an `error` ref, render a simple "failed to load, retry" state, matching the pattern already used correctly in `AdminView.vue`, `ImportView.vue`, `PostView.vue`, `ProfileView.vue`, `UploadView.vue`.
- **Effort**: S (mechanical, same fix repeated 7x — could delegate as one batch)

### M2 — Clickable `<div>`s are not keyboard-accessible
- **Files**:
  - `frontend/src/views/AdminView.vue:191` — `<div class="job-header" @click="job.expanded = !job.expanded">` (expand/collapse toggle)
  - `frontend/src/views/PostView.vue:62` — `<div class="sfw-overlay post-sfw-overlay" @click="reveal(post.id)">Click to reveal</div>`
  - `frontend/src/components/PostThumb.vue` (`sfw-overlay` div, same pattern) and `frontend/src/views/CollectionsView.vue`, `frontend/src/views/HomeView.vue` (same SFW-reveal overlay pattern)
- **Problem**: None of these have `role="button"`, `tabindex="0"`, or a keydown handler (verified via `grep -n "tabindex\|role=\"button\""` across these files — zero matches). A keyboard-only user cannot expand admin job rows or reveal SFW-blurred content.
- **Fix**: Either swap to `<button class="...">` (simplest, gets focus/keyboard/ARIA for free) or add `role="button" tabindex="0" @keydown.enter.space.prevent="handler"`.
- **Effort**: S

### M3 — Login/Register form inputs have no accessible label association
- **Files**:
  - `frontend/src/views/LoginView.vue:8-9` — username/password inputs rely on `placeholder` only, no `<label>` at all.
  - `frontend/src/views/RegisterView.vue:6-15` — `<label>` text is present but has no `for`/`id` pairing with its `<input>` (verified: no `for=` or `id=` attributes anywhere in either file).
- **Problem**: Screen readers can't programmatically associate the label with the field; placeholder-as-label also disappears once the user types, losing the only accessible name in LoginView.
- **Fix**: Add matching `id`/`for` pairs (or wrap input in `<label>`) on both views; add visible `<label>` elements to LoginView's username/password fields.
- **Effort**: S

### M4 — Fullscreen post image missing `alt`
- **File**: `frontend/src/views/PostView.vue:22-29` (the `v-else` fullscreen `<img :src="post?.file_url" ...>` inside the `<Teleport>` fullscreen viewer)
- **Problem**: No `alt` attribute, unlike the inline post image at line ~53 which correctly sets `:alt="post.title"`.
- **Fix**: Add `:alt="post?.title"` to match the inline image.
- **Effort**: S

### M5 — README documents a `register()` auth action that doesn't exist
- **Files**: `frontend/README.md:106` documents `register()` as a Pinia auth-store action (`POST /auth/register`); `frontend/src/stores/auth.js` only exports `{ user, loading, isAuthenticated, fetchUser, login, logout }` — no `register` function.
- **Problem**: Stale/incorrect docs — a contributor following the README's API table will look for a store action that isn't there. (`RegisterView.vue` presumably calls `api.post('/auth/register', ...)` directly instead — not itself a bug, but the doc is wrong.)
- **Fix**: Update the table to remove `register()` or note that registration is a direct `api.post` call from `RegisterView.vue`, not a store action.
- **Effort**: S

---

## Low

### L1 — Large unoptimized static GIFs served from `public/`
- **Files**: `frontend/public/static/image/429.gif` (2.4 MB), `404.gif` (1.9 MB), `dirt.gif` (724 KB), `403.gif` (296 KB), `418.gif` (225 KB)
- **Problem**: These error-page decorations total ~5.5 MB and are shipped unoptimized/uncompressed. They're low-traffic pages, so impact is limited, but they inflate the static asset footprint for no real benefit.
- **Fix**: Recompress with `gifsicle -O3` or convert to a short looping `<video>`/WebP if animation quality allows; not urgent since these are non-critical pages.
- **Effort**: S

### L2 — `frontend/README.md` file-tree is stale
- **File**: `frontend/README.md:19-45` (Project Structure tree)
- **Problem**: Tree lists `Pagination.vue` as the only component and omits `PostThumb.vue`, `useSfwMode.js` composable, and several views that exist in `src/views/` (`AdminView.vue`, `AdminUserEditView.vue`, `CollectionView.vue`, `FavouritesView.vue`, `ForbiddenView.vue`, `ImportView.vue`, `RateLimitView.vue`, `TeapotView.vue`).
- **Fix**: Regenerate the tree, or drop it in favor of pointing at `src/router/index.js` as the source of truth for routes.
- **Effort**: S

---

## Not flagged (checked, no issue found)

- **Auth token storage**: No JWT/token in `localStorage`/`sessionStorage` — auth uses httpOnly cookies + CSRF token fetched into memory (`frontend/src/api/client.js`), which is the correct pattern. `localStorage` use in `UploadView.vue` (upload draft) and `PostsView.vue` (wall-mode UI preference) is non-sensitive UX state, fine as-is.
- **`href`/URL injection**: No dynamically bound `href` attributes found in `frontend/src/**` (all navigation goes through `<router-link>` with template-literal paths built from known API fields, not raw user HTML).
- **Dependencies**: `frontend/package.json` is lean (5 runtime deps: vue, vue-router, pinia, axios, @vueuse/core) — no bloat, nothing to trim.
- **CSRF handling**: `frontend/src/api/client.js` correctly attaches `X-CSRFToken` on mutating requests and centrally redirects to a rate-limit view on 429.
- **SFW-blur composable**: `useSfwMode.js` is shared correctly across `PostThumb.vue`, `HomeView.vue`, `PostView.vue`, `CollectionsView.vue` — not duplicated logic, good reuse.

---

## Summary

- **High**: 1
- **Medium**: 5
- **Low**: 2
- **Total**: 8

The one real security finding is the unsanitized `v-html` in `ArticleView.vue`. The rest is missing error/loading states on a handful of simpler views and some accessibility gaps (keyboard access on custom clickable divs, unlabeled login inputs) — all mechanical, same-pattern fixes already used correctly elsewhere in the codebase. Auth/CSRF handling, dependency footprint, and href/URL handling are clean. No code was modified.
