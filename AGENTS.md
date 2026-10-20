# AGENTS instructions

## Environment Setup

- **Python 3.14**, managed with [uv](https://docs.astral.sh/uv/)
- **Node 24**, managed with [mise](https://mise.jdx.dev/)
- Install prek: `uv tool install prek`
- Enable commit hooks: `prek install`

## Commands

- Run python tests: `uv run pytest -xvs`
- Run a single test: `uv run pytest -xvs dusken/tests/test_user.py::TestName`
- Lint python with ruff only: `prek run ruff-check`
- Format python with ruff only: `prek run ruff-format`
- Build javascript: `mise run frontend-build`
- Lint javascript: `mise run frontend-lint`, or `prek run eslint` (needs `frontend/node_modules`)
- Format javascript: `mise run frontend-format`
- Run pre-commit checks on staged files: `prek run`
- Run pre-commit checks on all tracked files: `prek run -a`
- Make new files visible to prek: `git add -N <file>`
- Generate GraphQL schema: `mise run generate_schema`
- Load test fixtures: `uv run python manage.py loaddata testdata`
- Run dev server: `mise run run`
- Run frontend dev server: `mise run frontend-run`
- Run Celery worker: `mise run worker`
- Format and lint markdown `prek run rumdl`
- Extract translations: `mise run makemessages`
- Extract translations for a sub-app: `uv run ../../../manage.py makemessages -l nb` (from `dusken/apps/<app>/`)
- Compile translations: `mise run compilemessages`
- Edit translations: `mise run poedit [app]`

## Coding Conventions

- Max line length: 120 characters
- Ruff with nearly all rules enabled (see pyproject.toml) — docstrings and type annotations are NOT required
- ESLint flat config with Prettier formatting for JS
- Tests must not make network calls (pytest-socket enforced)
- Documentation uses rumdl for linting
- Django route names use kabab casing

## Commits

Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/),
e.g. `fix: restrict user update view to own profile or superuser`. Skip the body unless it carries
important information that isn't already in the code or comments. No trailers.

## Architecture

- **Django settings**: `dusken/settings/` — `base.py` (shared), `dev.py`, `prod.py`. Tests use `dev` settings.
- **Database routing**: Custom router in `dusken/router.py` routes LDAP and Kassa models to separate databases.
- **API layers**: REST (DRF) at `dusken/api/` and GraphQL (Strawberry) at `dusken/api/graphql.py`.
- **Templates**: Django templates with Bootstrap 5 in `dusken/templates/`.
- **Static assets**: Built by Rspack from `frontend/app/` into `staticfiles/`.
- **i18n**: Norwegian Bokmål (`nb`) translations in `dusken/locale/`, and in `dusken/apps/<app>/locale/` for
  sub-apps with their own (`neuf_auth`). Commit the compiled `.mo` files with the `.po` files.

## Local Services

Run `docker-compose up -d` to start required services:

- PostgreSQL (port 5432)
- Redis (port 6379)
- OpenLDAP (ports 389, 636)

SQLite is used by default in dev; Docker services are needed for LDAP and Celery features. Production runs
PostgreSQL, so migrations must work on both.

## CI Pipeline

A push to `main` runs, in `.gitea/workflows/`:

1. `prek` — all pre-commit hooks (ruff-check, ruff-format, django-upgrade, rumdl) except eslint
2. `tests` — frontend lint and build, Django migrations, `manage.py check`, pytest with coverage
3. `deploy` — once both pass, kaniko builds and pushes `git.neuf.no/edb/galtinn:<sha>`, then
   `ssh gitdeploy@amiga.neuf.no <sha>` deploys it. Both jobs run only while the repository variable
   `DEPLOY_AMIGA` is `true`.

Renovate runs daily from [edb/renovate-runner](https://git.neuf.no/edb/renovate-runner) as the `renovate` account.
`renovate.json` opens one grouped minor/patch PR and one lockfile maintenance PR on the first of each month. Majors,
Django feature releases and Python upgrades wait for approval on the Dependency Dashboard issue.

The deploy runs `migrate` before the new code starts, so a migration must work with the old code too, and it stays
applied after a rollback.

## Production

A docker compose stack in `/opt/galtinn` on amiga (services `app`, `worker`, `db`, `redis`), managed by
[edb-infra](https://git.neuf.no/edb/edb-infra) (`roles/galtinn.md`, usually checked out at `../edb-infra`).

- Log in as `deploy@amiga.neuf.no`, which has sudo.
- Back up the database before a risky migration: `sudo systemctl start galtinn-dump.service` writes a `pg_dump`
  into `/opt/galtinn/backup/`. Copy it to a name not starting with `galtinn-`, or the nightly prune deletes it
  after 7 days.
- Run Django commands: `sudo docker compose --project-directory /opt/galtinn exec app python manage.py <command>`

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
- `dusken/apps/` - Sub-apps (common, kassa, neuf_auth, neuf_ldap)
- `dusken/fixtures/` - Test data fixtures
- `docs/agents/` - Documentation of agent-driven changes
- `Dockerfile` - Production image, built and deployed by `.gitea/workflows/deploy.yaml`
