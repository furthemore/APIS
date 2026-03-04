#!/bin/sh

./manage.py migrate

case $1 in
    worker)
        celery -A fm_eventmanager worker --loglevel=info
        ;;

    *)
        exec /usr/bin/supervisord -c /app/supervisord.conf
        ;;
esac
