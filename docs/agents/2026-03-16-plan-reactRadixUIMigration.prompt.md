# Plan: Migrate to React + radix ui Frontend

Replace Django HTML templates with a React SPA using radix ui, incrementally migrating pages while Django continues serving non-migrated templates. Django serves the React SPA from the same origin using session-cookie auth. New API endpoints use DRF generic views. First phase covers **Auth + Home dashboard** to validate the approach.

## Architecture

- **React SPA** in new `web/` directory, built with **Vite + TypeScript**
- **Django** serves the SPA's `index.html` via a catch-all view for migrated routes
- **Session auth** via CSRF cookies — same origin, no CORS needed
- Old `frontend/` stays intact for non-migrated pages (Rspack builds legacy JS/CSS)
- **DRF generic views** for new endpoints; existing ViewSets stay unchanged
- **react-i18next** for Norwegian Bokmål + English
- GraphQL stays as-is

## Phase 1A: React App Scaffolding

1. **Create `web/` directory** — Vite + React + TypeScript scaffold (`index.html`, `vite.config.ts`, `tsconfig.json`, `package.json`, `src/main.tsx`, `src/App.tsx`)

2. **Set up radix ui** — match Bootstrap 5 color scheme where practical

3. **Set up React Router** — routes for login, register, home only; catch-all redirects to Django for non-migrated pages

4. **Set up react-i18next** — `web/src/i18n/` with `en.json` and `nb.json`, translate strings for migrated pages

5. **Create API client utility** (`web/src/lib/api.ts`) — reads CSRF token from cookie, attaches `X-CSRFToken` header, typed `fetchApi()` wrapper

6. **Add build/dev tasks** to `mise.toml` — `web-build` and `web-run`; Vite proxies `/api/` and `/admin/` to Django on port 8000

## Phase 1B: Django Backend Changes

7. **Create SPA-serving view** in `dusken/views/general.py` — `spa_view` decorated with `@ensure_csrf_cookie`, serves `web/dist/index.html`

8. **Add URL patterns** in `dusken/urls.py` for migrated routes (`login/`, `register/`, `home/`) pointing to `spa_view`

9. **Add Django settings** in `dusken/settings/base.py` — `WEB_DIR`, add `web/dist/` to `STATICFILES_DIRS`

10. **Create DRF auth endpoints** in new `dusken/api/views/auth.py` using APIView/generic views:
    - `POST /api/auth/login/` — accepts `{email, password}`, creates session, returns user data
    - `POST /api/auth/logout/` — destroys session
    - `GET /api/auth/session/` — returns current user or 401
    - `POST /api/auth/password/reset/` — sends reset email
    - `POST /api/auth/password/reset/confirm/` — validates token, sets password
    - `POST /api/auth/password/change/` — changes password (authenticated)

11. **Add membership types endpoint** — `GET /api/membership-types/` using `ListAPIView` with new `MembershipTypeSerializer`

12. **Enhance `/api/me/`** — add `email_is_confirmed`, `phone_number_confirmed` to `DuskenUserSerializer`

13. **Wire API URLs** in `dusken/api/urls.py`

14. **Update user registration endpoint** — also establish Django session on register (currently only returns token)

## Phase 1C: React Pages

15. **Auth context/hook** (`useAuth.ts`) — `AuthProvider` calls `GET /api/auth/session/` on mount, exposes `user`, `login()`, `logout()`, `register()`

16. **Login page** — shadcn Card with email + password form, error handling

17. **Register page** — form with reCAPTCHA, auto-login on success

18. **Home dashboard** — membership status card, email/phone validation prompts, buy membership button, member card display

19. **Layout components** — Navbar (shadcn NavigationMenu), language switcher, user dropdown, footer

20. **404 page** — links back to Django for non-migrated routes

## Phase 2+ (out of scope)

User profile, memberships list, volunteer dashboard, org unit management, stats, password reset UI, flatpages, account deletion, SMS activation.

## Relevant Files

### Create

- `web/` — entire React app directory
- `dusken/api/views/auth.py` — auth API views
- `dusken/api/serializers/auth.py` — auth serializers

### Modify

- `dusken/urls.py` — add SPA routes
- `dusken/views/general.py` — add `spa_view`
- `dusken/api/urls.py` — add auth + membership-type routes
- `dusken/api/serializers/users.py` — add validation status fields
- `dusken/settings/base.py` — `WEB_DIR`, `STATICFILES_DIRS`
- `mise.toml` — add web tasks

### Reference (patterns)

- `frontend/app/index.js` — CSRF handling pattern
- `dusken/api/views/users.py` — existing DRF view patterns
- `dusken/templates/dusken/home.html` — home page structure to replicate

## Verification

1. `cd web && npm run build` succeeds
2. Vite dev server (5173) proxies API to Django (8000) — login flow works end-to-end
3. New pytest tests in `dusken/tests/test_auth_api.py` for login/logout/session endpoints
4. Session persists across page refreshes
5. CSRF token flows correctly on mutating requests
6. Home page shows correct membership status and validation prompts
7. Language toggle works (EN/NB)
8. Non-migrated routes still serve Django templates
9. `uv run pytest -xvs` — all existing tests pass
10. `prek run` — all lint checks pass

## Decisions

- **Incremental migration** — React coexists with Django templates
- **`web/` separate from `frontend/`** — avoids breaking non-migrated pages
- **Session cookies** — same-origin, simplest security model
- **DRF generic views** for new endpoints; existing ViewSets unchanged
- **Django serves SPA** — single deployment, no CORS
- **Kebab-case route names** per project convention

## Further Considerations

1. **reCAPTCHA in React**: Need `react-google-recaptcha` or similar. Recommendation: add a `GET /api/config/` endpoint returning public keys (reCAPTCHA site key, Stripe public key).

2. **Dev workflow**: Vite proxies `/api/` to Django (option A) vs Django reverse-proxies to Vite (option B). Recommendation: **Option A** — standard Vite `server.proxy`, developer hits `localhost:5173`.

3. **Production static serving**: Vite build outputs hashed assets to `web/dist/assets/`. Add this to `STATICFILES_DIRS` for Django's `collectstatic` + `ManifestStaticFilesStorage`. Serve `index.html` separately via file read in `spa_view`.
