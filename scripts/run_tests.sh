#!/bin/sh
# to not use the AWS file storage
export TESTING_USE_DEFAULT_STORAGE=1
# to not use SMTP Email backend
export TESTING_USE_DEFAULT_EMAIL_BACKEND=1
# run in testing environment
# --parallel 4 # will spawn threads to speed up tests
# --keepdb # will the test database
python manage.py test --keepdb --settings=app.settings.testing