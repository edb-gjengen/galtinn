DUSKEN - Dårlig Utrustet Studentsystem som Kommer til å Endre Norge.

[![Build Status](https://circleci.com/gh/edb-gjengen/dusken.png)](https://circleci.com/gh/edb-gjengen/dusken)
[![codecov](https://codecov.io/gh/edb-gjengen/dusken/branch/master/graph/badge.svg)](https://codecov.io/gh/edb-gjengen/dusken)

## Install
    sudo apt install python3-venv libpq-dev python3-dev libsasl2-dev libldap2-dev libssl-dev ldap-utils redis-server
    python3 -m venv venv
    . venv/bin/activate
    pip install -U pip wheel
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python manage.py migrate
    python manage.py loaddata testdata
    python manage.py runserver
    celery -A duskensite worker -B  # In a new tab
    
    # Frontend
    npm install -g gulp-cli
    fab install  # cd dusken/static && yarn && gulp build
    fab serve
    
    # Add Stripe keys in duskensite/local_settings.py
    # Note: get this from your account on stripe.com

    # Add reCAPTCHA keys in duskensite/local_settings.py
    # As: RECAPTCHA_PUBLIC_KEY and RECAPTCHA_PRIVATE_KEY


### Useful local_settings.py

    AUTH_PASSWORD_VALIDATORS = []

### Tests

    python manage.py test dusken
    # Run this for testing import from Inside (legacy)
    python manage.py test --testrunner apps.inside.tests.NoDbTestRunner apps.inside
    
## Development
Font icons are from: https://linearicons.com/free

## Card payments
Dusken supports Stripe for card payments. The Stripe API's are documented here:

* Stripe Checkout (JS): https://stripe.com/docs/checkout
* Stripe API (Python): https://stripe.com/docs/api?lang=python

Use this VISA card for testing: 4242 4242 4242 4242

## System Configuration

To sell memberships exactly one `MembershipType` has to have the `is_default` flag set.

To indentify users as volunteers exactly one `GroupProfile` has to have `type` set to `GroupProfile.TYPE_VOLUNTEERS`.

## LDAP development
    # Run LDAP
    docker run -e LDAP_DOMAIN=neuf.no -e LDAP_ORGANISATION="Neuf" -e LDAP_ADMIN_PWD="toor" -p 389:389 -d nikolaik/openldap
    # Add testdata
    ldapadd -D "cn=admin,dc=neuf,dc=no" -w "toor" -f apps/neuf_ldap/tests/testdata.ldif  # Testdata

    # Configure our LDAP database like so in local_settings.py:
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': 'ldap://localhost/',
        'USER': 'cn=admin,dc=neuf,dc=no',
        'PASSWORD': 'toor',
    },