# -*- coding: utf-8 -*-
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
        'debug' : 'alert-info',
        'info' : 'alert-info',
        'success' : 'alert-success',
        'warning' : 'alert-warning',
        'error' : 'alert-danger'
    }

    if msg not in bootstrap.keys():
        return ''

    return bootstrap[msg]
     
