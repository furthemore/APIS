import django_u2f.urls
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r"^registration/", include("registration.urls")),
    url(r"^admin/", admin.site.urls),
    url(r"^u2f/", include(django_u2f.urls, namespace="u2f")),
]
