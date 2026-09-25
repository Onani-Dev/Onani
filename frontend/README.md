# Onani — Frontend

Vue 3 SPA for the Onani booru, served at `/`.

## Stack

- **Vue 3.5** with `<script setup>` SFCs
- **Vite 8** — dev server + build
- **Vue Router 4** — client routing (HTML5 history, base `/`)
- **Pinia 3** — state management
- **Axios** — HTTP client with automatic CSRF handling

## Project Structure

```
src/
├── main.js              Entry point
├── App.vue              Root component (router-view)
├── api/
│   └── client.js        Axios instance + CSRF helper
├── components/          Pagination.vue, PostThumb.vue, ...
├── composables/         useSfwMode.js, ...
├── layouts/
│   └── DefaultLayout.vue  Navbar + <slot/>
├── router/
│   └── index.js         Route definitions + auth guard (source of truth for routes)
├── stores/
│   └── auth.js          Auth state (Pinia)
└── views/                One component per route; see src/router/index.js for the full list.
```

## Development

```bash
npm install
npm run dev        # starts Vite dev server on :5173
```

The dev server proxies `/api` and `/static` to `http://localhost:5000`, so
the Flask backend must be running (either directly or via Docker).

## Building

```bash
npm run build      # outputs to dist/
npm run preview    # preview the production build locally
```

In Docker, the `frontend` service runs `npm run build` and copies `dist/`
for deployment artifacts. In the current repo setup:

- Dev profile (`podman-compose --profile dev`) runs a dedicated `frontend-dev`
  service with `npm run dev` for HMR on port `5173`.
- Prod profile (`podman-compose --profile prod`) serves the built frontend from
  the all-in-one `app` image (`Dockerfile`) via Caddy.

In production, you can either:

- Serve the built assets via Flask's SPA catch-all setup, or
- Serve them from your external reverse proxy/static host while proxying
  `/api` to Gunicorn.

## API Client (`src/api/client.js`)

A pre-configured Axios instance (`api`) with:

- **Base URL**: `/api/v1`
- **Credentials**: cookies included (`withCredentials: true`)
- **CSRF**: on the first mutating request (POST/PUT/PATCH/DELETE) the client
  fetches a token from `GET /auth/csrf` and caches it. All subsequent
  mutating requests include the `X-CSRFToken` header automatically.

```js
import api from '@/api/client'

const { data } = await api.get('/posts', { params: { page: 1 } })
```

## Auth Store (`src/stores/auth.js`)

Pinia store exposing:

| Member            | Type     | Description                          |
| ----------------- | -------- | ------------------------------------ |
| `user`            | ref      | Current user object or `null`        |
| `loading`         | ref      | `true` while initial auth check runs |
| `isAuthenticated` | computed | `!!user`                             |
| `fetchUser()`     | action   | `GET /auth/me`                       |
| `login()`         | action   | `POST /auth/login`                   |
| `logout()`        | action   | `POST /auth/logout`                  |

Registration is not a store action — `RegisterView.vue` calls
`POST /auth/register` directly via `api.post(...)`.

Routes with `meta: { requiresAuth: true }` are guarded by a
`router.beforeEach` hook that redirects unauthenticated users to `/login`.

## Adding a New View

1. Create `src/views/FooView.vue`.
2. Add a route in `src/router/index.js`:
   ```js
   {
     path: '/foo',
     name: 'foo',
     component: () => import('@/views/FooView.vue'),
     meta: { layout: DefaultLayout },
   }
   ```
3. (Optional) Add `meta: { requiresAuth: true }` for protected routes.

## Path Alias

`@` is aliased to `src/` in the Vite config, so imports look like:

```js
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
```
