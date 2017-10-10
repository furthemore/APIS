# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Room(models.Model):
	event = models.ForeignKey('registration.Event')
	name = models.CharField(max_length=100)
	def __str__(self):
		return self.name

class Panelist(models.Model):
	event = models.ForeignKey('registration.Event')
	first_name = models.CharField(max_length=50,blank=True)
	last_name = models.CharField(max_length=50,blank=True)
	fan_name = models.CharField(max_length=50)
	badge = models.ForeignKey('registration.Badge',blank=True,null=True)
	email = models.EmailField(blank=True)
	checked_in = models.BooleanField(default=False)
	checked_in_date = models.DateTimeField(blank=True,null=True)
	def __str__(self):
		return self.fan_name

class Track(models.Model):
	title = models.CharField(max_length=120)
	description = models.TextField(blank=True,null=True)
	color = models.CharField(max_length=7,default='#')
	def __str__(self):
		return self.title

class Panel(models.Model):
	DURATION = (
			(30,"30 Minutes"),
			(30*2,"1 Hour"),
			(30*3,"1.5 Hours"),
			(30*4,"2 Hours"),
			(30*5,"2.5 Hours"),
			(30*6,"3 Hours"),
			(30*7,"3.5 Hours"),
			(30*8,"4 Hours"),
			(30*9,"4.5 Hours"),
			(30*10,"5 Hours"),
			(30*11,"5.5 Hours"),
			(30*12,"6 Hours"),
			(30*13,"6.5 Hours"),
			(30*14,"7 Hours"),
			(30*15,"7.5 Hours"),
			(30*16,"8 Hours"),
			(30*17,"8.5 Hours"),
			(30*18,"9 Hours"),
			(30*19,"9.5 Hours"),
			(30*20,"10 Hours"),
			(30*21,"10.5 Hours"),
			(30*22,"11 Hours"),
			(30*23,"11.5 Hours"),
			(30*24,"12 Hours"),
			(30*25,"12.5 Hours"),
			(30*26,"13 Hours"),
			(30*27,"13.5 Hours"),
			(30*28,"14 Hours"),
			(30*29,"14.5 Hours"),
			(30*30,"15 Hours"),
			(30*31,"15.5 Hours"),
			(30*32,"16 Hours"),
			(30*33,"16.5 Hours"),
			(30*34,"17 Hours"),
			(30*35,"17.5 Hours"),
			(30*36,"18 Hours"),
			(30*37,"18.5 Hours"),
			(30*38,"19 Hours"),
			(30*39,"19.5 Hours"),
			(30*40,"20 Hours"),
			(30*41,"20.5 Hours"),
			(30*42,"21 Hours"),
			(30*43,"21.5 Hours"),
			(30*44,"22 Hours"),
			(30*45,"22.5 Hours"),
			(30*46,"23 Hours"),
			(30*47,"23.5 Hours"),
			(30*48,"24 Hours"),
		)
	EVENT_TYPES = (
			(0,"Panel"),
			(1,"Blackout"),
			(2,"Convention Event"),
			(3,"Convention Ops"),
		)
	SETUP_TIME = (
			(0, "No Setup Time"),
			(15, "15 Minutes"),
			(30, "30 Minutes"),
			(60, "1 Hour"),
			(90, "1.5 Hours"),
			(120, "2 Hours"),
			(150, "2.5 Hours"),
			(180, "3 Hours"),
		)
	event = models.ForeignKey('registration.Event')
	panelist = models.ForeignKey(Panelist,blank=True,null=True)
	# to be removed for PanelSlot
	room = models.ForeignKey(Room)

	track = models.ForeignKey(Track,blank=True,null=True)

	title = models.CharField(max_length=200)

	description = models.TextField(blank=True)

	r18 = models.BooleanField(default=False)

	accepted = models.BooleanField(default=False)
	confirmed = models.BooleanField(default=False)

	# to be removed for PanelSlot
	time_start = models.DateTimeField()

	# to be removed for PanelSlot
	duration = models.IntegerField(choices=DURATION,default=60)

	# to be removed for Track
	type = models.IntegerField(choices=EVENT_TYPES,default=0)

	# to be removed for PanelSlot
	setup_time = models.IntegerField(choices=SETUP_TIME,default=30)

	def __str__(self):
		return self.title

class PanelRequestType(models.Model):
	event = models.ForeignKey('registration.Event')
	EVENT_TYPES = (
			(0,"Panel"),
			(1,"Blackout"),
			(2,"Convention Event"),
			(3,"Convention Ops"),
		)
	panel_type = models.IntegerField(choices=EVENT_TYPES,default=0)
	title = models.CharField(max_length=100)
	description = models.TextField(blank=True)

class PanelRequest(models.Model):
	panel = models.ForeignKey(Panel)
	request_type = models.ForeignKey(PanelRequestType)
	# requested
	# false = don't require, would be nice to have
	# true  = need, would require
	requested = models.BooleanField(default=False)
	confirmed = models.BooleanField(default=False)
	date_updated = models.DateTimeField(auto_now_add=True)

class PanelComment(models.Model):
	panel = models.ForeignKey(Panel)
	user = models.ForeignKey(User)
	show_to_panelist = models.BooleanField(default=False)
	comment = models.TextField()
	date_added = models.DateTimeField(auto_now_add=True)

class PanelSlot(models.Model):
	DURATIONS = (
			(15,"0 Hours, 15 Minutes"),
			(15*2,"0 Hours, 30 Minutes"),
			(15*3,"0 Hours, 45 Minutes"),
			(15*4,"1 Hour, 0 Minutes"),
			(15*5,"1 Hour, 15 Minutes"),
			(15*6,"1 Hour, 30 Minutes"),
			(15*7,"1 Hour, 45 Minutes"),
			(15*8,"2 Hours, 0 Minutes"),
			(15*9,"2 Hours, 15 Minutes"),
			(15*10,"2 Hours, 30 Minutes"),
			(15*11,"2 Hours, 45 Minutes"),
			(15*12,"3 Hours, 0 Minutes"),
			(15*13,"3 Hours, 15 Minutes"),
			(15*14,"3 Hours, 30 Minutes"),
			(15*15,"3 Hours, 45 Minutes"),
			(15*16,"4 Hours, 0 Minutes"),
			(15*17,"4 Hours, 15 Minutes"),
			(15*18,"4 Hours, 30 Minutes"),
			(15*19,"4 Hours, 45 Minutes"),
			(15*20,"5 Hours, 0 Minutes"),
			(15*21,"5 Hours, 15 Minutes"),
			(15*22,"5 Hours, 30 Minutes"),
			(15*23,"5 Hours, 45 Minutes"),
			(15*24,"6 Hours, 0 Minutes"),
			(15*25,"6 Hours, 15 Minutes"),
			(15*26,"6 Hours, 30 Minutes"),
			(15*27,"6 Hours, 45 Minutes"),
			(15*28,"7 Hours, 0 Minutes"),
			(15*29,"7 Hours, 15 Minutes"),
			(15*30,"7 Hours, 30 Minutes"),
			(15*31,"7 Hours, 45 Minutes"),
			(15*32,"8 Hours, 0 Minutes"),
			(15*33,"8 Hours, 15 Minutes"),
			(15*34,"8 Hours, 30 Minutes"),
			(15*35,"8 Hours, 45 Minutes"),
			(15*36,"9 Hours, 0 Minutes"),
			(15*37,"9 Hours, 15 Minutes"),
			(15*38,"9 Hours, 30 Minutes"),
			(15*39,"9 Hours, 45 Minutes"),
			(15*40,"10 Hours, 0 Minutes"),
			(15*41,"10 Hours, 15 Minutes"),
			(15*42,"10 Hours, 30 Minutes"),
			(15*43,"10 Hours, 45 Minutes"),
			(15*44,"11 Hours, 0 Minutes"),
			(15*45,"11 Hours, 15 Minutes"),
			(15*46,"11 Hours, 30 Minutes"),
			(15*47,"11 Hours, 45 Minutes"),
			(15*48,"12 Hours, 0 Minutes"),
			(15*49,"12 Hours, 15 Minutes"),
			(15*50,"12 Hours, 30 Minutes"),
			(15*51,"12 Hours, 45 Minutes"),
			(15*52,"13 Hours, 0 Minutes"),
			(15*53,"13 Hours, 15 Minutes"),
			(15*54,"13 Hours, 30 Minutes"),
			(15*55,"13 Hours, 45 Minutes"),
			(15*56,"14 Hours, 0 Minutes"),
			(15*57,"14 Hours, 15 Minutes"),
			(15*58,"14 Hours, 30 Minutes"),
			(15*59,"14 Hours, 45 Minutes"),
			(15*60,"15 Hours, 0 Minutes"),
			(15*61,"15 Hours, 15 Minutes"),
			(15*62,"15 Hours, 30 Minutes"),
			(15*63,"15 Hours, 45 Minutes"),
			(15*64,"16 Hours, 0 Minutes"),
			(15*65,"16 Hours, 15 Minutes"),
			(15*66,"16 Hours, 30 Minutes"),
			(15*67,"16 Hours, 45 Minutes"),
			(15*68,"17 Hours, 0 Minutes"),
			(15*69,"17 Hours, 15 Minutes"),
			(15*70,"17 Hours, 30 Minutes"),
			(15*71,"17 Hours, 45 Minutes"),
			(15*72,"18 Hours, 0 Minutes"),
			(15*73,"18 Hours, 15 Minutes"),
			(15*74,"18 Hours, 30 Minutes"),
			(15*75,"18 Hours, 45 Minutes"),
			(15*76,"19 Hours, 0 Minutes"),
			(15*77,"19 Hours, 15 Minutes"),
			(15*78,"19 Hours, 30 Minutes"),
			(15*79,"19 Hours, 45 Minutes"),
			(15*80,"20 Hours, 0 Minutes"),
			(15*81,"20 Hours, 15 Minutes"),
			(15*82,"20 Hours, 30 Minutes"),
			(15*83,"20 Hours, 45 Minutes"),
			(15*84,"21 Hours, 0 Minutes"),
			(15*85,"21 Hours, 15 Minutes"),
			(15*86,"21 Hours, 30 Minutes"),
			(15*87,"21 Hours, 45 Minutes"),
			(15*88,"22 Hours, 0 Minutes"),
			(15*89,"22 Hours, 15 Minutes"),
			(15*90,"22 Hours, 30 Minutes"),
			(15*91,"22 Hours, 45 Minutes"),
			(15*92,"23 Hours, 0 Minutes"),
			(15*93,"23 Hours, 15 Minutes"),
			(15*94,"23 Hours, 30 Minutes"),
			(15*95,"23 Hours, 45 Minutes"),
			(15*96,"24 Hours, 0 Minutes"),
			(15*97,"24 Hours, 15 Minutes"),
			(15*98,"24 Hours, 30 Minutes"),
			(15*99,"24 Hours, 45 Minutes"),
		)
	SETUP_TIMES = (
			(0, "No Setup Time"),
			(15, "15 Minutes"),
			(30, "30 Minutes"),
			(60, "1 Hour"),
			(90, "1.5 Hours"),
			(120, "2 Hours"),
			(150, "2.5 Hours"),
			(180, "3 Hours"),
		)
	event = models.ForeignKey('registration.Event')
	panel = models.ForeignKey(Panel,blank=True,null=True)
	label = models.CharField(max_length=20,blank=True,null=True)
	setup_notes = models.TextField(blank=True,null=True)
	time_start = models.DateTimeField()
	duration = models.IntegerField(choices=DURATIONS,default=15*4)
	setup_time = models.IntegerField(choices=SETUP_TIMES,default=0)
	room = models.ForeignKey(Room)
	def __str__(self):
		return self.panel.title
	
