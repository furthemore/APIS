#!/bin/sh

uv run ./manage.py migrate

exec /usr/bin/supervisord -c /app/supervisord.conf
