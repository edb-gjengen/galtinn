# Galtinn

Membership system ++ for DNS / Chateau Neuf.

[![Pipeline Status](https://git.neuf.no/edb/galtinn/badges/main/pipeline.svg)](https://git.neuf.no/edb/galtinn/-/commits/main)
[![Coverage](https://git.neuf.no/edb/galtinn/badges/main/coverage.svg)](https://git.neuf.no/edb/galtinn)

## Install

```bash
sudo apt install python3-venv libpq-dev python3-dev libsasl2-dev libldap2-dev libssl-dev ldap-utils
poetry shell  # Start a poetry shell creating a virtual environment.
poetry install
pre-commit install
python manage.py migrate
python manage.py loaddata testdata
bin/run

# Frontend
bin/build-frontend
bin/run-frontend

# start databases
docker-compose up
# start Celery worker
bin/worker

# Add Stripe keys in dusken/settings/local.py
# Note: get this from your account on stripe.com
# Add reCAPTCHA keys in dusken/settings/local.py as:
# RECAPTCHA_PUBLIC_KEY and RECAPTCHA_PRIVATE_KEY
```

## Useful dusken/settings/local.py

```python
AUTH_PASSWORD_VALIDATORS = []
```

### Tests

```bash
# Make sure redis is running using `docker-compose up`
bin/test
# Run this for testing import from Inside (legacy)
python manage.py test --testrunner apps.inside.tests.NoDbTestRunner apps.inside
```

## Development

Font icons are from: <https://linearicons.com/free>

### Card payments

Dusken supports Stripe for card payments. The Stripe APIs are documented here:

- Stripe Checkout (JS): <https://docs.stripe.com/payments/checkout>
- Stripe API (Python): <https://stripe.com/docs/api?lang=python>

Use this VISA card for testing: 4242 4242 4242 4242

Run the stripe CLI to forward webhooks locally:

```sh
stripe listen --forward-to localhost:8000/api/stripe/webhook/
```

### LDAP

```bash
# Run LDAP
docker run -e LDAP_DOMAIN=neuf.no -e LDAP_ORGANISATION="Neuf" -e LDAP_ADMIN_PWD="toor" -p 389:389 -d nikolaik/openldap
# Add testdata
ldapadd -D "cn=admin,dc=neuf,dc=no" -w "toor" -f apps/neuf_ldap/tests/testdata.ldif  # Testdata
```

Configure our LDAP database like so in `dusken/settings/local.py`:

```python
DATABASES = {
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': 'ldap://localhost/',
        'USER': 'cn=admin,dc=neuf,dc=no',
        'PASSWORD': 'toor',
    }
}
```

### Translations

```bash
# Generate .po files based on translation strings in code and template files
fab makemessages
# Only for app dusken
fab makemessages:limit=dusken
```

## System Configuration

To sell memberships exactly one `MembershipType` has to have the `is_default` flag set.

To indentify users as volunteers exactly one `GroupProfile` has to have `type` set to `GroupProfile.TYPE_VOLUNTEERS`.

## Dusken

Galtinn was called DUSKEN during development - _Dårlig Utrustet Studentsystem som Kommer til å Endre Norge._

## OpenID Connect - OIDC

Galtinn has OIDC support. The `/api/me/oauth/` endpoint supports oauth2 tokens. The rest of the API endpoints do not. Though the ID token and the standard `/api/oauth/userinfo` endpoint provides enough data

### Configure private key

```sh
# Generate a private key
openssl genrsa -out oidc.key 4096
# Set key in OIDC_RSA_PRIVATE_KEY env variable
```

### Configure your OIDC Oauth2 application

Navigate to `/admin/oauth2_provider/application/` and create an application with the following details:

- `Name`: Pick a descriptive name for your app, f.ex "Discord bot"
- `Redirect URI`: Where the user will be redirected after login and authorizing in Galtinn.
- `Client Type`: Public
- `Authorization grant type`: Authorization code
- `Algorithm`: RSA with SHA-2 256

### Example authorization code PKCE flow

Navigate to the following URL in your browser:

Generate the `code_challenge` hash:

```sh
openssl rand -hex 16
echo -n "<random value>" | sha256sum | awk '{ print $1}' | base64 | sed 's/.$//'
```

```text
http://localhost:8000/api/oauth/authorize/?client_id=1nxL1CkKfZQ7unBH5SFiWlXJt9YB0eYihBwrmdQW&scope=openid%20profile%20email&response_type=code&redirect_uri=http://localhost:8000/api/oauth/generic-callback&code_challenge=ZGY3ZGI1ODU1MWQ5MTA5MjFhOGFiMjk4YzUwYjI3MDlkOGM1ODVhMmFlOGU2OWQ1ZmEzMjAyOTE0MjRiMGZjZQo
```

The URL above includes the following:

- `client_id`: Copy from the application you made
- `scope`: `openid profile email`
- `response_type`: `code`
- `redirect_uri`: Needs to match a URI from the application you made
- `code_challenge`: Client generated hash from above

_Note that I tried adding `code_challenge_method`: `S256`, but could not get it to work. You might have better luck 🤞_

After the user accepts, the browser is redireted to `redirect_uri` with the granted `code` as a query param.

The client then exchanges the authorization code with a token using a request similar to:

```sh
curl -d "grant_type=authorization_code" -d 'client_id=1nxL1CkKfZQ7unBH5SFiWlXJt9YB0eYihBwrmdQW' -d "code=p8sO5IyrpExeKsqpWar84CnFonqU9v" -d 'redirect_uri=<http://localhost:8000/api/oauth/generic-callback>' -d "code_verifier=ZGY3ZGI1ODU1MWQ5MTA5MjFhOGFiMjk4YzUwYjI3MDlkOGM1ODVhMmFlOGU2OWQ1ZmEzMjAyOTE0MjRiMGZjZQo" <http://localhost:8000/api/oauth/token/>
```

The request above includes the data `grant_type=authorization_code`, `client_id=<client_id>` and:

- `code`: Returned with the redirect_uri above as a query param
- `redirect_uri` Same as the first request
- `code_verifier` The same value as `code_challenge` in the first request

The client can then use the `access_token` in the response from the previous request to send a new request for profile details:

```sh
$ curl -s -H "Authorization: Bearer <access_token>" http://localhost:8000/api/oauth/userinfo/ | jq .
{
  "sub": "1",
  "family_name": "Adminson",
  "given_name": "Admin",
  "name": "Admin Adminson ",
  "preferred_username": "admin",
  "updated_at": "2024-04-02T12:17:23.022109+00:00",
  "email": "admin@example.com",
  "email_verified": false,
  "is_volunteer": false,
  "is_member": false
}
```

Read more:

- <https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#openid-connect-support>
- <https://auth0.com/docs/authenticate/login/oidc-conformant-authentication/oidc-adoption-auth-code-flow>
- <https://docs.digdir.no/docs/idporten/oidc/oidc_func_pkce.html>
