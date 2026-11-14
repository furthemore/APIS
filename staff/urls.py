from django.urls import path

import staff.views

app_name = "staff"

urlpatterns = [
    path("", staff.views.index, name="index"),
    path("portal/", staff.views.profile, name="portal"),
    path("openings/", staff.views.openings, name="openings"),
    path("apply/<str:token>/", staff.views.apply, name="apply"),
    path("application/<str:token>/", staff.views.application, name="application"),
    path("register/complete/", staff.views.register_complete, name="register_complete"),
    path("register/<str:token>/", staff.views.register, name="register"),
]
