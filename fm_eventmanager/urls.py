import django_u2f.urls
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from django.http import HttpResponse

admin.autodiscover()

urlpatterns = [
    url(
        r"robots.txt",
        lambda x: HttpResponse("User-Agent: *\n\nDisallow: /", content_type="text/plain"),
        name="robots_file"
    ),
    url(r"^registration/", include("registration.urls", namespace="registration")),
    url(r"^admin/", admin.site.urls),
    url(r"^u2f/", include(django_u2f.urls, namespace="u2f")),
    url(r"^$", RedirectView.as_view(url="registration"), name="root"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
