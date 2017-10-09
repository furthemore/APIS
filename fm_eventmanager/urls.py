from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^registration/', include('registration.urls')),
    url(r'^backend/events/', include('events.urls')),
    url(r'^backend/volunteer/', include('volunteer.urls')),
    url(r'^admin/', admin.site.urls),
]
