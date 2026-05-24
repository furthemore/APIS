import json
import logging

from django.conf import settings
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from square.utils.webhooks_helper import verify_signature

from registration import payments
from registration.models import PaymentWebhookNotification
from registration.views import common

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def square_webhook(request):
    square_signature = request.headers.get("X-Square-HMACSHA256-Signature")
    notification_url = request.build_absolute_uri()

    signature_valid = verify_signature(
        request_body=request.body.decode("utf-8"),
        signature_header=square_signature,
        signature_key=settings.SQUARE_WEBHOOK_SIGNATURE_KEY,
        notification_url=notification_url,
    )

    if not signature_valid:
        logger.warning(
            "Invalid webhook signature",
            extra={"notification_url": notification_url},
        )
        return common.abort(403, "Forbidden: invalid signature")

    try:
        request_body = json.loads(request.body)
    except (ValueError, json.JSONDecodeError):
        return common.abort(400, "Unable to decode JSON")

    if "event_id" not in request_body:
        return common.abort(400, "Missing event_id")

    event_id = request_body["event_id"]
    event_type = request_body.get("type")

    # Check to see if webhook was already stored:
    existing = PaymentWebhookNotification.objects.filter(event_id=event_id)
    if existing.exists():
        return common.success(200)

    # Store the verified event notification
    notification = PaymentWebhookNotification(
        event_id=event_id,
        event_type=event_type,
        body=request_body,
        headers=dict(request.headers),
    )
    try:
        notification.save()
    except IntegrityError:
        logger.info(
            "Duplicate webhook event_id received",
            extra={"event_id": event_id},
        )
        return common.success(200)

    process_webhook(notification)

    return common.success(200)


def process_webhook(notification: PaymentWebhookNotification):
    logger.info(
        "Processing webhook notification",
        extra={
            "event_id": notification.event_id,
            "event_type": notification.body.get("type"),
        },
    )
    result = False
    if notification.body["type"] == "refund.updated":
        result = payments.process_webhook_refund_update(notification)
    elif notification.body["type"] == "refund.created":
        result = payments.process_webhook_refund_created(notification)
    elif notification.body["type"] == "payment.updated":
        result = payments.process_webhook_payment_updated(notification)
    elif notification.body["type"] in ("dispute.created", "dispute.state.updated"):
        result = payments.process_webhook_dispute_created_or_updated(notification)
    else:
        logger.warning(
            "Unhandled webhook event type",
            extra={"event_type": notification.body.get("type"), "event_id": notification.event_id},
        )

    notification.processed = result
    notification.save()
