from django import template
from django.utils.timezone import timedelta

register = template.Library()


@register.inclusion_tag("templatetags/basic_attendee_form.html")
def show_attendee_form(*args, **kwargs):
    return kwargs


@register.inclusion_tag("templatetags/online_price_types.html")
def show_price_types(*args, **kwargs):
    return kwargs


@register.inclusion_tag("templatetags/basic_staff_form.html")
def show_staff_form(*args, **kwargs):
    return kwargs


@register.simple_tag
def attendee_get_first(attendee):
    firstName = attendee.get("firstName", "")
    preferredName = attendee.get("preferredName")

    if preferredName:
        return preferredName
    return firstName


@register.simple_tag
def selected_if_month(date, value):
    if hasattr(date, "month") and date.month == value:
        return "selected"
    return ""


@register.simple_tag
def subtract_years(date, years):
    return date.replace(year=date.year - years).strftime("%B %e, %Y")
