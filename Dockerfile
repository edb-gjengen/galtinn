FROM node:24-trixie-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
# --ignore-scripts skips husky's prepare hook, which needs a git checkout
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build -- --env production

FROM python:3.14-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
# python-ldap and mysqlclient ship no wheels; git fetches the django-ldapdb fork
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git pkg-config libldap2-dev libsasl2-dev \
       default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY . .
COPY --from=frontend /src/frontend/dist frontend/dist
RUN DJANGO_SETTINGS_MODULE=dusken.settings.prod .venv/bin/python manage.py collectstatic --noinput

FROM python:3.14-slim-trixie
RUN apt-get update \
    && apt-get install -y --no-install-recommends libldap2 libsasl2-2 libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 931 --home-dir /app --no-create-home galtinn
COPY --from=build /app /app
WORKDIR /app
ARG SENTRY_RELEASE=N/A
ENV PATH=/app/.venv/bin:$PATH \
    DJANGO_SETTINGS_MODULE=dusken.settings.prod \
    PYTHONUNBUFFERED=1 \
    SENTRY_RELEASE=$SENTRY_RELEASE
USER galtinn
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "dusken.wsgi"]
