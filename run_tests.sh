#!/bin/sh
# can use below variable to not use the AWS file storage
#export TESTING_USE_DEFAULT_STORAGE=1
# run in testing environment
python manage.py test --settings=app.settings.testing