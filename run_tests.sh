#!/bin/sh
# can use below variable to not use the AWS file storage
export TESTING_USE_DEFAULT_STORAGE=1
# run in testing environment
# --parallel 4 # will spawn threads to speed up tests
# --keepdb # will the test database
python manage.py test --keepdb --settings=app.settings.testing