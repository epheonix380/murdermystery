#!/bin/sh
# Container start: bring the database up to date, load the cases, then serve.
set -e
python manage.py migrate --noinput
python manage.py import_case
exec daphne --bind 127.0.0.1 --port "${PORT:-8100}" --proxy-headers mystery.asgi:application
