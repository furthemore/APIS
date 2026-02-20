import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fm_eventmanager.settings")

app = Celery("fm_eventmanager")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
