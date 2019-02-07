#!/bin/bash

VIRTUAL_ENV=".venv"

echo -n "Reset local database? (y/N) "
read ANSWER
if [ "$ANSWER" != "y" ]; then
    exit
fi
ENGINE="$($VIRTUAL_ENV/bin/python manage.py get_settings_value DATABASES default,ENGINE)"
if [ "$ENGINE" == "django.db.backends.postgresql" ]; then
    DATABASE="$($VIRTUAL_ENV/bin/python manage.py get_settings_value DATABASES default,NAME)"
    USER="$($VIRTUAL_ENV/bin/python manage.py get_settings_value DATABASES default,USER)"
    psql -U postgres -c "DROP DATABASE $DATABASE"
    psql -U postgres -c "CREATE DATABASE $DATABASE OWNER $USER"
elif [ "$ENGINE" == "django.db.backends.sqlite3" ]; then
    FILE="$($VIRTUAL_ENV/bin/python manage.py get_settings_value DATABASES default,NAME)"
    rm -f $FILE
    echo rm -f $FILE
fi
