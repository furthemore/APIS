import django_u2f.urls
from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from django.views.generic import RedirectView
from django.http import HttpResponse

admin.autodiscover()

urlpatterns = [
    re_path(
        r"robots.txt",
        lambda x: HttpResponse("User-Agent: *\n\nDisallow: /", content_type="text/plain"),
        name="robots_file"
    ),
    path("registration/", include("registration.urls", namespace="registration")),
    re_path(r"^admin/", admin.site.urls),
    path("u2f/", include(django_u2f.urls, namespace="u2f")),
    path("", RedirectView.as_view(url="registration"), name="root"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
