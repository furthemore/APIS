from django.conf.urls import include, url
from django.contrib import admin
import django_u2f.urls

admin.autodiscover()

urlpatterns = [
    url(r'^registration/', include('registration.urls')),
    url(r'^backend/events/', include('events.urls')),
    url(r'^backend/volunteer/', include('volunteer.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^u2f/', include(django_u2f.urls, namespace='u2f')),
]
