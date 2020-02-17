# -*- coding: utf-8 -*-
import datetime

from django import template
from django.contrib.sites.models import Site

register = template.Library()


@register.simple_tag
def current_domain():
    return Site.objects.get_current().domain


@register.simple_tag
def current_site_name():
    return Site.objects.get_current().name


@register.simple_tag
def bootstrap_message(msg):
    """
    Translates Django message tags into bootstrap alert classes
    """
    bootstrap = {
        "debug": "alert-info",
        "info": "alert-info",
        "success": "alert-success",
        "warning": "alert-warning",
        "error": "alert-danger",
    }

    if msg not in bootstrap.keys():
        return ""

    return bootstrap[msg]


@register.simple_tag
def js_date(date):
    return "Date({0}, {1}, {2})".format(date.year, date.month - 1, date.day)


@register.simple_tag
def event_start_date(event):
    """
    Returns a "sliding" event date:
        event.startDate if startDate is in the future, otherwise
        today's date, up to the event endDate

    :param event: event
    :return: javascript-formatted date object
    """
    today = datetime.datetime.now().date()
    if today < event.eventStart:
        return js_date(event.eventStart)
    else:
        if today > event.eventEnd:
            return js_date(event.eventEnd)
        return js_date(today)
