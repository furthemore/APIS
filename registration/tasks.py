import logging

from celery import shared_task

from registration import emails

logger = logging.getLogger("registration.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_registration_email_task(self, order_id, email, send_vip=True):
    from registration.models import Order

    try:
        order = Order.objects.get(id=order_id)
        emails.send_registration_email(order, email, send_vip)
    except Exception as exc:
        logger.exception("Failed to send registration email for order %s", order_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_upgrade_instructions_task(self, badge_id):
    from registration.models import Badge

    try:
        badge = Badge.objects.get(id=badge_id)
        emails.send_upgrade_instructions(badge)
    except Exception as exc:
        logger.exception("Failed to send upgrade instructions for badge %s", badge_id)
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
            "Failed to send upgrade payment email for attendee %s order %s",
            attendee_id,
            order_id,
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_registration_email_task(self, order_id):
    try:
        emails.send_staff_registration_email(order_id)
    except Exception as exc:
        logger.exception(
            "Failed to send staff registration email for order %s", order_id
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_promotion_email_task(self, staff_id):
    from registration.models import Staff

    try:
        staff = Staff.objects.get(id=staff_id)
        emails.send_staff_promotion_email(staff)
    except Exception as exc:
        logger.exception("Failed to send staff promotion email for staff %s", staff_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_new_staff_email_task(self, token_id):
    from registration.models import TempToken

    try:
        token = TempToken.objects.get(id=token_id)
        emails.send_new_staff_email(token)
    except Exception as exc:
        logger.exception("Failed to send new staff email for token %s", token_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_application_email_task(self, dealer_id):
    try:
        emails.send_dealer_application_email(dealer_id)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer application email for dealer %s", dealer_id
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
            "Failed to send dealer assistant form email for dealer %s", dealer_id
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dealer_assistant_email_task(self, dealer_id):
    try:
        emails.send_dealer_assistant_email(dealer_id)
    except Exception as exc:
        logger.exception(
            "Failed to send dealer assistant email for dealer %s", dealer_id
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
            "Failed to send dealer assistant registration invite for assistant %s",
            assistant_id,
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
            "Failed to send dealer payment email for dealer %s order %s",
            dealer_id,
            order_id,
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
            "Failed to send dealer approval emails for dealers %s", dealer_ids
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
            "Failed to send chargeback notice email for order %s", order_id
        )
        raise self.retry(exc=exc)
