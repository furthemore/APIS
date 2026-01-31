import os
import sys

from django.core.asgi import get_asgi_application

sys.path.append("/app/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fm_eventmanager.settings")

application = get_asgi_application()
