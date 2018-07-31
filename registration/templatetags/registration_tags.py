from django import template

register = template.Library()

@register.inclusion_tag('templatetags/basic_attendee_form.html')
def show_attendee_form(attendee=None, emailOptions=False):
    return {'attendee': attendee, 'emailOptions': emailOptions}

@register.inclusion_tag('templatetags/online_price_types.html')
def show_price_types():
    return {}

@register.inclusion_tag('templatetags/basic_staff_form.html')
def show_staff_form(staff=None, badge=None):
    return {'staff': staff, 'badge': badge}
