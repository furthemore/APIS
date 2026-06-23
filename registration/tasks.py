import logging

from celery import shared_task

from registration import emails

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_registration_email_task(self, order_id, email, send_vip=True):
    from registration.models import Order

    try:
        order = Order.objects.get(id=order_id)
        emails.send_registration_email(order, email, send_vip)
    except Exception as exc:
        logger.exception(
            "Failed to send registration email",
            extra={"order_id": order_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_upgrade_instructions_task(self, badge_id):
    from registration.models import Badge

    try:
        badge = Badge.objects.get(id=badge_id)
        emails.send_upgrade_instructions(badge)
    except Exception as exc:
        logger.exception(
            "Failed to send upgrade instructions",
            extra={"badge_id": badge_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_upgrade_payment_email_task(self, attendee_id, order_id):
    from registration.models import Attendee, Order

    try:
        attendee = Attendee.objects.get(id=attendee_id)
        order = Order.objects.get(id=order_id)
        emails.send_upgrade_payment_email(attendee, order)
    except Exception as exc:
        logger.exception(
            "Failed to send upgrade payment email",
            extra={"attendee_id": attendee_id, "order_id": order_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_registration_email_task(self, order_id):
    try:
        emails.send_staff_registration_email(order_id)
    except Exception as exc:
        logger.exception(
            "Failed to send staff registration email",
            extra={"order_id": order_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_promotion_email_task(self, staff_id):
    from registration.models import Staff

    try:
        staff = Staff.objects.get(id=staff_id)
        emails.send_staff_promotion_email(staff)
    except Exception as exc:
        logger.exception(
            "Failed to send staff promotion email",
            extra={"staff_id": staff_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_new_staff_email_task(self, token_id):
    from registration.models import StaffInvite

    try:
        token = StaffInvite.objects.get(id=token_id)
        emails.send_new_staff_email(token)
    except Exception as exc:
        logger.exception(
            "Failed to send new staff email",
            extra={"token_id": token_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_application_email_task(self, dealer_id):
    try:
        emails.send_dealer_application_email(dealer_id)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer application email",
            extra={"dealer_id": dealer_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_assistant_form_email_task(self, dealer_id):
    from registration.models import Dealer

    try:
        dealer = Dealer.objects.get(id=dealer_id)
        emails.send_dealer_assistant_form_email(dealer)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer assistant form email",
            extra={"dealer_id": dealer_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_assistant_email_task(self, dealer_id):
    try:
        emails.send_dealer_assistant_email(dealer_id)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer assistant email",
            extra={"dealer_id": dealer_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_assistant_registration_invite_task(self, assistant_id):
    from registration.models import DealerAsst

    try:
        assistant = DealerAsst.objects.get(id=assistant_id)
        emails.send_dealer_assistant_registration_invite(assistant)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer assistant registration invite",
            extra={"assistant_id": assistant_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_payment_email_task(self, dealer_id, order_id):
    from registration.models import Dealer, Order

    try:
        dealer = Dealer.objects.get(id=dealer_id)
        order = Order.objects.get(id=order_id)
        emails.send_dealer_payment_email(dealer, order)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer payment email",
            extra={"dealer_id": dealer_id, "order_id": order_id},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_approval_email_task(self, dealer_ids):
    from registration.models import Dealer

    try:
        dealers = Dealer.objects.filter(id__in=dealer_ids)
        emails.send_dealer_approval_email(dealers)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer approval emails",
            extra={"dealer_ids": dealer_ids},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_chargeback_notice_email_task(self, order_id):
    from registration.models import Order

    try:
        order = Order.objects.get(id=order_id)
        emails.send_chargeback_notice_email(order)
    except Exception as exc:
        logger.exception(
            "Failed to send chargeback notice email",
            extra={"order_id": order_id},
        )
        raise self.retry(exc=exc)
