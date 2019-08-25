"""
WSGI config for fm_eventmanager project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

#import os, sys

#from django.core.wsgi import get_wsgi_application

#sys.path.append('/home/rechner/workspace')
#sys.path.append('/home/root/projects/furthemore-py3/APIS/')
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fm_eventmanager.settings")

#application = get_wsgi_application()

import os, sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/root/')
sys.path.append('/root/projects/')
sys.path.append('/root/projects/furthemore-py3/')
sys.path.append('/root/projects/furthemore-py3/APIS/')
sys.path.append('/root/projects/furthemore-py3/APIS/fm_eventmanager')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fm_eventmanager.settings')

application = get_wsgi_application()

