DUSKEN - Dårlig Utrustet Studentsystem som Kommer til å Endre Norge.

[![Build Status](https://circleci.com/gh/edb-gjengen/dusken.png)](https://circleci.com/gh/edb-gjengen/dusken)
[![codecov](https://codecov.io/gh/edb-gjengen/dusken/branch/master/graph/badge.svg)](https://codecov.io/gh/edb-gjengen/dusken)

## Install
    sudo apt install python3-venv libpq-dev python3-dev libssl-dev
    python3 -m venv venv
    . venv/bin/activate
    pip install -U pip wheel
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python manage.py migrate
    python manage.py loaddata testdata
    python manage.py runserver
    
    # Frontend
    npm install -g gulp-cli bower
    fab install  # cd dusken/static && npm install && bower install && gulp build
    fab serve
    
    # Add Stripe keys in duskensite/local_settings.py
    # Note: get this from your account on stripe.com

### Useful local_settings.py

    AUTH_PASSWORD_VALIDATORS = []
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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

To sell memberships at least one `MembershipType` has to have the `is_default` flag set.
