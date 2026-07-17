"""
Celery tasks for staff-related operations
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_invitation_email_task(self, invite_id):
    """
    Send staff invitation email asynchronously.
    """
    from staff.models import StaffInvite
    import staff.emails

    try:
        invite = StaffInvite.objects.get(id=invite_id)
        staff.emails.send_staff_invitation_email(invite)
    except Exception as exc:
        logger.exception(
            "Failed to send staff invitation email",
            extra={"invite_id": invite_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_promotion_email_task(self, staff_id, token):
    """
    Send staff promotion email asynchronously.
    """
    from staff.models import Staff
    import staff.emails

    try:
        staff_profile = Staff.objects.get(id=staff_id)
        staff.emails.send_staff_promotion_email(staff_profile, token)
    except Exception as exc:
        logger.exception(
            "Failed to send staff promotion email",
            extra={"staff_id": staff_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_registration_confirmation_task(self, staff_id, event_registration_id, reference=None):
    """
    Send staff registration confirmation email asynchronously.
    """
    from staff.models import Staff, StaffEventRegistration
    import staff.emails

    try:
        staff_profile = Staff.objects.get(id=staff_id)
        event_registration = StaffEventRegistration.objects.get(id=event_registration_id)
        staff.emails.send_staff_registration_confirmation(staff_profile, event_registration, reference)
    except Exception as exc:
        logger.exception(
            "Failed to send staff registration confirmation email",
            extra={"staff_id": staff_id, "event_registration_id": event_registration_id},
        )
        raise self.retry(exc=exc)
