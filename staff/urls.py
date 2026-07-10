from django.urls import path

import staff.views

app_name = "staff"

urlpatterns = [
    path("", staff.views.index, name="index"),
    path("profile/", staff.views.profile, name="profile"),
    path("openings/", staff.views.openings, name="openings"),
    path("apply/<int:posting_id>/", staff.views.apply, name="apply"),
    path("application/<int:applicant_id>/", staff.views.application, name="application"),
    path("portal/", staff.views.portal, name="portal"),
    path("register/complete/", staff.views.register_complete, name="register_complete"),
    path("register/<str:token>/", staff.views.register, name="register"),
]
