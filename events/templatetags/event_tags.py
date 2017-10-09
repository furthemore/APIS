from django import template
from events.models import Track
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def track_display(track):
	return mark_safe("<svg width='10' height='10'><rect width='10' height='10' style='fill:"+track.color+";stroke-width:1;stroke:rgb(0,0,0)'></svg> "+track.title)

@register.simple_tag
def track_list(event,type):
	tracks = Track.objects.all().order_by('title')
	ni = ""
	for x in tracks:
		ni = ni + "<a href='/backend/events/manage/"+str(event.pk)+"/manager/track/"+str(x.pk)+"/' class='"+type+"'><svg width='10' height='10'><rect width='10' height='10' style='fill:"+x.color+";stroke-width:1;stroke:rgb(0,0,0)'></svg> "+x.title+"</a>"
	return mark_safe(ni)
