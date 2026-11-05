"""
Staff-related email functions
"""
from django.template.loader import render_to_string

from registration.emails import send_email
from registration.models import Event
import registration.views.staff


def send_staff_invitation_email(invite):
    """
    Send invitation email to new staff member.
    Uses StaffInvite token.
    """
    event = Event.objects.get(default=True)
    data = {
        "registrationToken": invite.token,
        "event": event
    }
    
    msg_txt = render_to_string("staff/emails/invitation.txt", data)
    msg_html = render_to_string("staff/emails/invitation.html", data)
    staff_email = registration.views.staff.get_staff_email(event)
    
    send_email(
        staff_email,
        [invite.email],
        f"Welcome to {event.name} Staff!",
        msg_txt,
        msg_html,
    )


def send_staff_promotion_email(staff_profile, token):
    """
    Send promotion email when an attendee is promoted to staff.
    Uses staff.registration_token.
    """
    from registration.models import Event
    
    event = Event.objects.get(default=True)
    data = {
        "registrationToken": token,
        "event": event,
        "staff": staff_profile
    }
    
    msg_txt = render_to_string("staff/emails/promotion.txt", data)
    msg_html = render_to_string("staff/emails/promotion.html", data)
    staff_email = registration.views.staff.get_staff_email(event)
    
    send_email(
        staff_email,
        [staff_profile.email],
        f"Congratulations! Promoted to {event.name} Staff",
        msg_txt,
        msg_html,
    )


def send_staff_registration_confirmation(staff_profile, event_registration, reference=None):
    """
    Send confirmation email after staff completes registration.
    """
    from registration.models import Event
    
    event = event_registration.event
    staff_email = registration.views.staff.get_staff_email(event)
    
    data = {
        "event": event,
        "staff_name": staff_profile.first_name(),
        "reference": reference,
        "staff_email": staff_email,
    }
    
    msg_txt = render_to_string("staff/emails/confirmation.txt", data)
    msg_html = render_to_string("staff/emails/confirmation.html", data)
    
    send_email(
        staff_email,
        [staff_profile.email],
        f"Registration Confirmed - {event.name}",
        msg_txt,
        msg_html,
    )
