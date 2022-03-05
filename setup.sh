#!/bin/bash

python manage.py makemigrations rfis
python manage.py makemigrations
python manage.py migrate rfis
python manage.py migrate
python manage.py initialsetup