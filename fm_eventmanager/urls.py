from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.generic import RedirectView

admin.autodiscover()

urlpatterns = [
    re_path(
        r"robots.txt",
        lambda x: HttpResponse(
            "User-Agent: *\n\nDisallow: /", content_type="text/plain"
        ),
        name="robots_file",
    ),
    path("registration/", include("registration.urls", namespace="registration")),
    path("staff/", include("staff.urls", namespace="staff")),
    re_path(r"^admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", RedirectView.as_view(url="registration"), name="root"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
