#/bin/bash

virtualenv venv -p python3
source venv/bin/activate

pip install -q -r requirements.txt

python manage.py test
