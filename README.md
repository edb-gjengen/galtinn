DUSKEN - Dårlig Utrustet Studentsystem som Kommer til å Endre Norge.

[![Build Status](https://travis-ci.org/edb-gjengen/dusken.svg?branch=master)](https://travis-ci.org/edb-gjengen/dusken)
[![Coverage Status](https://coveralls.io/repos/edb-gjengen/dusken/badge.svg?branch=master&service=github)](https://coveralls.io/github/edb-gjengen/dusken?branch=master)

# Install
    sudo apt install python-virtualenv libpq-dev python3-dev
    virtualenv venv -p python3
    . venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

# Tests

    python manage.py test
