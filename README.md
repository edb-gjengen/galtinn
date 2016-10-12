DUSKEN - Dårlig Utrustet Studentsystem som Kommer til å Endre Norge.

[![Build Status](https://travis-ci.org/edb-gjengen/dusken.svg?branch=master)](https://travis-ci.org/edb-gjengen/dusken)
[![Coverage Status](https://coveralls.io/repos/edb-gjengen/dusken/badge.svg?branch=master&service=github)](https://coveralls.io/github/edb-gjengen/dusken?branch=master)

## TODO
* Set password
* Member cards
* Renewal

## Install
    sudo apt install python3-venv libpq-dev python3-dev
    pyvenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py loaddata testdata
    python manage.py runserver
    
    # Frontend
    npm install -g gulp-cli bower
    cd dusken/static
    npm install && bower install
    gulp build
    gulp serve
    
    # Add Stripe keys in duskensite/local_settings.py
    # Note: get this from your account on stripe.com

### Tests

    python manage.py test dusken
    # Run this for testing import from Inside (legacy)
    python manage.py test --testrunner apps.inside.tests.NoDbTestRunner apps.inside
    
## Development
Font icons are from: https://linearicons.com/free

## Card payments
Dusken supports Stripe for Card Payments

Docs:

* Stripe Checkout (JS): https://stripe.com/docs/checkout
* Stripe API (Python): https://stripe.com/docs/api?lang=python

Test VISA card: 4242 4242 4242 4242

## System Configuration

To sell memberships at least one `MembershipType` has to have the `is_default` flag set.
