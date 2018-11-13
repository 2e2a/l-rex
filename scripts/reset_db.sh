#!/bin/bash

VIRTUAL_ENV=".venv"

echo -n "Reset local database? (y/N)"
read ANSWER
if [ "$ANSWER" != "y" ]; then
    exit
fi
DATABASE="$($VIRTUAL_ENV/bin/python manage.py get_settings_value DATABASES default,NAME)"
USER="$($VIRTUAL_ENV/bin/python manage.py get_settings_value DATABASES default,USER)"
psql -U postgres -c "DROP DATABASE $DATABASE"
psql -U postgres -c "CREATE DATABASE $DATABASE OWNER $USER"

