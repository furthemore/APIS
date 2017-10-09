from django.conf.urls import url

from . import views

app_name = 'volunteer'

urlpatterns = [
	url(r'^master/(?P<event_id>[\w-]+)/$', views.master, name='master'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/requests/$', views.ControlsV1EventRequests, name='controls-v1-event-requests'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/requests/(?P<request_id>[\w-]+)/done/$', views.ControlsV1EventRequestsDone, name='controls-v1-event-requests-done'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/$', views.ControlsV1EventVolunteers, name='controls-v1-event-volunteers'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/recent/$', views.ControlsV1EventRecent, name='controls-v1-event-recent'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/register/$', views.ControlsV1EventRegister, name='controls-v1-event-register'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/$', views.ControlsV1EventVolunteer, name='controls-v1-event-volunteer'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/checkin/$', views.ControlsV1EventVolunteerCheckIn, name='controls-v1-event-volunteer-checkin'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/clockin/$', views.ControlsV1EventVolunteerClockIn, name='controls-v1-event-volunteer-clockin'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/clockout/$', views.ControlsV1EventVolunteerClockOut, name='controls-v1-event-volunteer-clockout'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/clockin/long/$', views.ControlsV1EventVolunteerClockInLong, name='controls-v1-event-volunteer-clockin-long'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/clockout/long/$', views.ControlsV1EventVolunteerClockOutLong, name='controls-v1-event-volunteer-clockout-long'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/volunteers/(?P<volunteer_id>[\w-]+)/timesheet/$', views.ControlsV1EventVolunteerTimesheet, name='controls-v1-event-volunteer-timesheet'),
]
