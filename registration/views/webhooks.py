import json
import logging

from django.conf import settings
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from square.utilities.webhooks_helper import is_valid_webhook_event_signature

from registration import payments
from registration.models import PaymentWebhookNotification
from registration.views import common

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def square_webhook(request):
    square_signature = request.headers.get("X-Square-HMACSHA256-Signature")
    notification_url = request.build_absolute_uri()

    signature_valid = is_valid_webhook_event_signature(
        request.body.decode("utf-8"),
        square_signature,
        settings.SQUARE_WEBHOOK_SIGNATURE_KEY,
        notification_url,
    )

    if not signature_valid:
        logger.warning("Invalid signature in Square request")
        common.abort(403, "Forbidden: invalid signature")

    try:
        request_body = json.loads(request.body)
    except (ValueError, json.JSONDecodeError):
        return common.abort(400, "Unable to decode JSON")

    if "event_id" not in request_body:
        return common.abort(400, "Missing event_id")

    event_id = request_body["event_id"]

    # Store the verified event notification
    notification = PaymentWebhookNotification(
        event_id=event_id, body=request_body, headers=dict(request.headers)
    )
    try:
        notification.save()
    except IntegrityError:
        return common.abort(409, f"Conflict: event_id {event_id} already exists")

    return common.success(200)


def process_webhook(notification):
    if notification.body["type"] == "refund.updated":
        result = payments.process_webhook_update(notification)
    elif notification.body["type"] == "refund.created":
        result = payments.process_webhook_created(notification)

    notification.processed = result
    notification.save()
