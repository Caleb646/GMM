#!/bin/sh
set -e  # Configure shell so that if one command fails, it exits

while true; do
    read -p "Have you read through the deployment checklist? " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done


pip freeze > requirements.txt
git add .
git commit -m "$1"
git push heroku-staging master