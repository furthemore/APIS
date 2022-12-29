import json
import logging

from django.conf import settings
from django.views.decorators.http import require_POST
from square.utilities.webhooks_helper import is_valid_webhook_event_signature

from registration.models import PaymentWebhookNotification
from registration.views import common

logger = logging.getLogger(__name__)


@require_POST
def square_webhook(request):
    try:
        request_body = json.loads(request.body)
    except (ValueError, json.JSONDecodeError):
        return common.abort(400, "Unable to decode JSON")

    if "event_id" not in request_body:
        return common.abort(400, "Missing event_id")

    event_id = request_body["event_id"]
    square_signature = request.headers.get("X-Square-HMACSHA256-Signature")
    notification_url = request.build_absolute_uri()

    signature_valid = is_valid_webhook_event_signature(
        request_body,
        square_signature,
        settings.SQUARE_WEBHOOK_SIGNATURE_KEY,
        notification_url,
    )

    if not signature_valid:
        logger.warning("Invalid signature in Square request")
        common.abort(403, "Forbidden: invalid signature")

    # Store the verified event notification
    notification = PaymentWebhookNotification(
        event_id=event_id, body=request_body, headers=request.headers
    )
    try:
        notification.save()
    except PaymentWebhookNotification.IntegrityError:
        return common.abort(409, f"Conflict: event_id {event_id} already exists")
