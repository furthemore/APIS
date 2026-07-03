from django.urls import path

import staff.views

app_name = "staff"

urlpatterns = [
    path("openings/", staff.views.openings, name="openings"),
    path("apply/", staff.views.apply, name="apply"),
    path("application/", staff.views.application, name="application"),
    path("portal/", staff.views.portal, name="portal"),
]
