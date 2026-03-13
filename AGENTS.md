# AGENTS instructions

## Environment Setup

- **Python 3.14**, managed with [uv](https://docs.astral.sh/uv/)
- **Node 24**, managed with [mise](https://mise.jdx.dev/)
- Install prek: `uv tool install prek`
- Enable commit hooks: `prek install`

## Commands

- Run python tests: `uv run pytest -xvs`
- Run a single test: `uv run pytest -xvs dusken/tests/test_user.py::TestName`
- Lint python with ruff only: `prek run ruff`
- Format python with ruff only: `prek run ruff-format`
- Build javascript: `mise run frontend-build`
- Lint javascript: `mise run frontend-lint`
- Format javascript: `mise run frontend-format`
- Run all pre-commit checks: `prek run`
- Generate GraphQL schema: `mise run generate_schema`
- Load test fixtures: `uv run python manage.py loaddata testdata`
- Run dev server: `mise run run`
- Run frontend dev server: `mise run frontend-run`
- Run Celery worker: `mise run worker`
- Format and lint markdown `prek run rumdl`

## Coding Conventions

- Max line length: 120 characters
- Ruff with nearly all rules enabled (see pyproject.toml) — docstrings and type annotations are NOT required
- ESLint flat config with Prettier formatting for JS
- Tests must not make network calls (pytest-socket enforced)
- Documentation uses rumdl for linting

## Architecture

- **Django settings**: `dusken/settings/` — `base.py` (shared), `dev.py`, `prod.py`. Tests use `dev` settings.
- **Database routing**: Custom router in `dusken/router.py` routes LDAP, Kassa, and tekstmelding models to separate databases.
- **API layers**: REST (DRF) at `dusken/api/` and GraphQL (Strawberry) at `dusken/api/graphql.py`.
- **Templates**: Django templates with Bootstrap 5 in `dusken/templates/`.
- **Static assets**: Built by Rspack from `frontend/app/` into `staticfiles/`.
- **i18n**: Norwegian Bokmål (`nb`) translations in `dusken/locale/`.

## Local Services

Run `docker-compose up -d` to start required services:

- PostgreSQL (port 5432)
- Redis (port 6379)
- OpenLDAP (ports 389, 636)

SQLite is used by default in dev; Docker services are needed for LDAP and Celery features.

## CI Pipeline

Push to `main` triggers deployment after:

1. `prek` — all pre-commit hooks (ruff, ruff-format, eslint)
2. `tests` — frontend build + Django migrations + pytest with coverage

## Repository structure

Python and JavaScript repository

- `.gitea/workflows` - GitHub Actions workflows ran using [act](https://github.com/nektos/act)
- `frontend/` - Frontend using vanilla JavaScript
- `dusken/` - Python/Django Backend using Django HTML templates and Bootstrap
- `dusken/api/` - REST and GraphQL API layer
- `dusken/models/` - Django models (users, orders, logs)
- `dusken/views/` - Django views
- `dusken/settings/` - Settings split into base/dev/prod
- `dusken/tests/` - pytest test suite
- `dusken/apps/` - Sub-apps (kassa, neuf_auth, neuf_ldap, tekstmelding)
- `dusken/fixtures/` - Test data fixtures
- `docs/agents/` - Documentation of agent-driven changes
- `bin/deploy` - Production deployment script
