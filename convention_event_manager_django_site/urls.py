from django.conf import settings
from django.contrib import admin
from django.views.generic import RedirectView
from django.http import HttpResponse
from django.urls import include, path
# import django_u2f.urls

admin.autodiscover()

urlpatterns = [
    path(
        "robots.txt",
        lambda x: HttpResponse(
            "User-Agent: *\n\nDisallow: /", content_type="text/plain"
        ),
        name="robots_file",
    ),
    path(
        "registration/", 
        include(
            f"{settings.CONVENTION_NAME}_registration.urls", 
            namespace=f"{settings.CONVENTION_NAME}_registration"
    )),
    path("admin/", admin.site.urls),
    # path("u2f/", include(django_u2f.urls, namespace="u2f")),
    path("", RedirectView.as_view(url="registration"), name="root"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
