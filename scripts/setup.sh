#!/bin/bash

python manage.py makemigrations rfis
python manage.py makemigrations database
python manage.py makemigrations
python manage.py migrate rfis
python manage.py migrate database
python manage.py migrate
python manage.py initialsetup
python manage.py collectstatic --noinput