from django.conf.urls import url

from . import views

app_name = 'events'

urlpatterns = [
	url(r'^panels/(?P<event_id>[\w-]+)/testform/$', views.testform, name='testform'),
	url(r'^manage/(?P<event_id>[\w-]+)/checkin/$', views.checkIn, name='checkin'),
	url(r'^manage/(?P<event_id>[\w-]+)/manager/$', views.manager, name='manager'),
	url(r'^manage/(?P<event_id>[\w-]+)/manager/track/(?P<track_id>[\w-]+)/$', views.manager, name='manager-track'),
	url(r'^manage/(?P<event_id>[\w-]+)/panel/(?P<panel_id>[\w-]+)/$', views.panelDetail, name='panel-detail'),
	url(r'^manage/(?P<event_id>[\w-]+)/visual/$', views.visual, name='visual'),
	url(r'^manage/(?P<event_id>[\w-]+)/glance/$', views.glance, name='glance'),	
	url(r'^controls/v1/pull/events/(?P<event>[\w-]+)/$', views.ControlsV1PullEvents, name='ControlsV1PullEvents'),
	url(r'^controls/v1/pull/events/(?P<event>[\w-]+)/(?P<timecode>[\w-]+)/$', views.ControlsV1PullEventsTimecode, name='ControlsV1PullEventsTimecode'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/$', views.ControlsV1GetEventDetail, name='ControlsV1GetEventDetail'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/panelist/(?P<panelist_id>[\w-]+)/checkin/$', views.ControlsV1CheckInPanelist, name='ControlsV1CheckInPanelist'),
	url(r'^controls/v1/(?P<event_id>[\w-]+)/panel/(?P<panel_id>[\w-]+)/verification/$', views.ControlsV1PullPanelVerification, name='ControlsV1PullPanelVerification'),	
	url(r'^controls/v1/(?P<event_id>[\w-]+)/panels/$', views.ControlsV1GetPanels, name='ControlsV1GetPanels'),	
	url(r'^controls/v1/(?P<event_id>[\w-]+)/rooms/$', views.ControlsV1GetRooms, name='ControlsV1GetRooms'),
	url(r'^controls/v1/helpers/blocks/$', views.ControlsV1Blocks, name='blocks'),
	url(r'^controls/v1/helpers/reverseblocks/$', views.ControlsV1ReverseBlocks, name='reverseblocks'),
]
