from django.urls import path

import staff.views

app_name = "staff"

urlpatterns = [
    path("", staff.views.index, name="index"),
    path("openings/", staff.views.openings, name="openings"),
    path("apply/<int:posting_id>/", staff.views.apply, name="apply"),
    path("application/<int:applicant_id>/", staff.views.application, name="application"),
    path("portal/", staff.views.portal, name="portal"),
]
