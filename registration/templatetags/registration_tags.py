from django import template

register = template.Library()

@register.inclusion_tag('templatetags/basic_attendee_form.html')
def show_attendee_form(*args, **kwargs):
    return kwargs

@register.inclusion_tag('templatetags/online_price_types.html')
def show_price_types(*args, **kwargs):
    return kwargs

@register.inclusion_tag('templatetags/basic_staff_form.html')
def show_staff_form(*args, **kwargs):
    return kwargs
