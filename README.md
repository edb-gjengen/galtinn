DUSKEN - Dårlig Utrustet Studentsystem som Kommer til å Endre Norge.

# Install
    sudo apt install python-virtualenv
    virtualenv venv -p python3
    . venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

# Tests

    python manage.py test
