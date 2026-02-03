#!/bin/sh

./manage.py migrate

exec /usr/bin/supervisord -c /app/supervisord.conf
