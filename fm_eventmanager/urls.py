import django_u2f.urls
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r"^registration/", include("registration.urls", namespace="registration")),
    url(r"^admin/", admin.site.urls),
    url(r"^u2f/", include(django_u2f.urls, namespace="u2f")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [url(r"^__debug__/", include(debug_toolbar.urls)),] + urlpatterns
