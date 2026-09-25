# Audit backlog (2026-09-25)

Detail reports: [security](security.md) · [infra](infra.md) · [backend-quality](backend-quality.md) · [frontend-qol](frontend-qol.md)

Totals: security 7H/6M/8L · infra 2H/4M/3L · backend 2H/4M/3L · frontend 1H/5M/2L

## Tier 1: fix first (chain to remote code execution / account takeover)
| ID | Issue | Effort |
|---|---|---|
| sec H1 | v1 API is CSRF-exempt (`routes/api/v1/__init__.py:15`) and remember cookie has no SameSite | S |
| sec H2 | DB restore pipes an upload into `psql`, so `\!` runs shell commands (`services/maintenance.py:228`) | M |
| sec H6 + infra H | Default `admin`/`admin` owner account; Postgres published on 5432 with a default password | S |
| sec H5 | Plaintext password stored in the session cookie (`auth.py:54`, `profile.py:156`) | S |
| sec H3/H4 | Privilege escalation: EDIT_USERS can grant ADMINISTRATION; ADMIN can create OWNER | S |
| sec H7 | A library path of `/` serves the whole filesystem to anonymous visitors | S |
| fe H | Unsanitised `v-html` in `ArticleView.vue:5` | S |

## Tier 2: correctness
- backend H: race between stop-scan and the task's final commit (the stop can be reverted); double scan start
- sec M1: SSRF through importers; M2: sessions survive a password change; M6: hidden posts readable by id; M4: thumbnail disk fill; M3: plaintext gallery-dl cookies
- infra H: containers run as root; `npm audit fix` (4 high); TensorFlow requirement back at `>=2.16` although 9ae1f2f pinned `==2.14`

## Tier 3: quality-of-life
- About 500 lines of dead `controllers/database/*`, and the tests cover the dead copies instead of `services/*`
- Missing error/loading states in 7 views; accessibility (clickable divs, unlabelled login fields)
- Caddy security headers, healthchecks, pinned Python lockfile, README drift (`register()`), large GIFs
- The test suite has no baseline: pytest never ran (no environment set up)
