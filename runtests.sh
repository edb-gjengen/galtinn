#/bin/bash

virtualenv venv
source venv/bin/activate

pip install -q -r requirements.txt

export SECRET_KEY='secret'
python manage.py test
