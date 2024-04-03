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

* Stripe Checkout (JS): <https://stripe.com/docs/checkout>
* Stripe API (Python): <https://stripe.com/docs/api?lang=python>

Use this VISA card for testing: 4242 4242 4242 4242

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

## TODO

* [ ] Replace user queries with graphql
* [ ] Delete user mutation
* [ ] Membership payment API v2
