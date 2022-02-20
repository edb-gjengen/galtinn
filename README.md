DUSKEN - Dårlig Utrustet Studentsystem som Kommer til å Endre Norge.

[![Build Status](https://circleci.com/gh/edb-gjengen/dusken.png)](https://circleci.com/gh/edb-gjengen/dusken)
[![codecov](https://codecov.io/gh/edb-gjengen/dusken/branch/master/graph/badge.svg)](https://codecov.io/gh/edb-gjengen/dusken)

## Install

```bash
sudo apt install python3-venv libpq-dev python3-dev libsasl2-dev libldap2-dev libssl-dev ldap-utils redis-server
poetry shell  # Start a poetry shell creating a virtual environment.
poetry install
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
```

# Add Stripe keys in duskensite/local_settings.py
# Note: get this from your account on stripe.com

# Add reCAPTCHA keys in duskensite/local_settings.py
# As: RECAPTCHA_PUBLIC_KEY and RECAPTCHA_PRIVATE_KEY

### Useful duskensite/settings/local.py

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

Font icons are from: https://linearicons.com/free

### Card payments

Dusken supports Stripe for card payments. The Stripe APIs are documented here:

* Stripe Checkout (JS): https://stripe.com/docs/checkout
* Stripe API (Python): https://stripe.com/docs/api?lang=python

Use this VISA card for testing: 4242 4242 4242 4242

### LDAP

```bash
# Run LDAP
docker run -e LDAP_DOMAIN=neuf.no -e LDAP_ORGANISATION="Neuf" -e LDAP_ADMIN_PWD="toor" -p 389:389 -d nikolaik/openldap
# Add testdata
ldapadd -D "cn=admin,dc=neuf,dc=no" -w "toor" -f apps/neuf_ldap/tests/testdata.ldif  # Testdata
```

Configure our LDAP database like so in `duskensite/settings/local.py`:

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

## Mailchimp

- Settings: `MAILCHIMP_LIST_ID`, `MAILCHIMP_WEBHOOK_SECRET`, `MAILCHIMP_API_KEY`, `MAILCHIMP_API_URL`
- Set up a webhook with unsubscribes using [this guide](http://kb.mailchimp.com/integrations/api-integrations/how-to-set-up-webhooks) (via API should be unchecked).
- The webhook URL path is: `/mailchimp/incoming/?secret=WEBHOOK_SECRET/`.

# TODO

- django-bootstrap5