from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch

from registration.models import PaymentWebhookNotification


class TestSquareWebhooks(TestCase):
    EVENT_ID = "9c7300fc-5b0d-3ffb-8cd0-c2987b21099c"
    WEBHOOK_BODY = """{"merchant_id":"PXRNP8VV5DSQH","type":"refund.updated","event_id":"9c7300fc-5b0d-3ffb-8cd0-c2987b21099c","created_at":"2022-12-29T06:30:29.411Z","data":{"type":"refund","id":"HH2sTvwhwFGq0Ivi4uBRvFJt55ZZY_rui4h8ypOw5yihLEBc5UC2HqJS0xUl7gukSQ7lq1AuF","object":{"refund":{"amount_money":{"amount":9000,"currency":"USD"},"created_at":"2022-12-29T06:30:27.642Z","destination_type":"CARD","id":"HH2sTvwhwFGq0Ivi4uBRvFJt55ZZY_rui4h8ypOw5yihLEBc5UC2HqJS0xUl7gukSQ7lq1AuF","location_id":"MESD3N22DWR0F","order_id":"gzamDxDtniM1nKbkDYZHYH0xbEOZY","payment_id":"HH2sTvwhwFGq0Ivi4uBRvFJt55ZZY","reason":" [rechner]","status":"COMPLETED","updated_at":"2022-12-29T06:30:29.404Z","version":6}}}}"""
    SHA256_SIGNATURE = "iGNztY3PcgdIv2MD97jZ7oOpcSk5FnyLdPnmn2MRx64="
    SIGNATURE_KEY = "bj-4rZKxCc8_1CZtghoatg"
    NOTIFICATION_URL = "https://webhook.site/5477eda8-952e-4844-91db-8b10cf228833"

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_square_webhook(self, mock_build_absolute_uri):
        mock_build_absolute_uri.return_value = self.NOTIFICATION_URL

        response = self.client.post(
            reverse("registration:square_webhook"),
            self.WEBHOOK_BODY,
            content_type="application/json",
            HTTP_X_SQUARE_HMACSHA256_SIGNATURE=self.SHA256_SIGNATURE,
        )

        self.assertTrue(response.status_code, 200)
        webhook = PaymentWebhookNotification.objects.get(event_id=self.EVENT_ID)
        self.assertEqual(str(webhook.event_id), webhook.body["event_id"])

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_square_webhook_invalid_signature(self, mock_build_absolute_uri):
        mock_build_absolute_uri.return_value = self.NOTIFICATION_URL

        response = self.client.post(
            reverse("registration:square_webhook"),
            self.WEBHOOK_BODY,
            content_type="application/json",
            HTTP_X_SQUARE_HMACSHA256_SIGNATURE="iGNztY3PcgdIv2MD86jZ7oOpcSk5FnyLdPnmn2MRx64=",
        )

        self.assertTrue(response.status_code, 403)

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("square.utilities.webhooks_helper.is_valid_webhook_event_signature")
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_square_webhook_invalid_json(
        self, mock_build_absolute_uri, mock_is_valid_webhook_event_signature
    ):
        mock_build_absolute_uri.return_value = self.NOTIFICATION_URL
        mock_is_valid_webhook_event_signature.return_value = True

        response = self.client.post(
            reverse("registration:square_webhook"),
            '{"foo',
            content_type="application/json",
            HTTP_X_SQUARE_HMACSHA256_SIGNATURE=self.SHA256_SIGNATURE,
        )

        self.assertTrue(response.status_code, 400)
        self.assertIn(b"Unable to decode JSON", response.content)

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("square.utilities.webhooks_helper.is_valid_webhook_event_signature")
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_square_webhook_missing_event_id(
        self, mock_build_absolute_uri, mock_is_valid_webhook_event_signature
    ):
        mock_build_absolute_uri.return_value = self.NOTIFICATION_URL
        mock_is_valid_webhook_event_signature.return_value = True

        response = self.client.post(
            reverse("registration:square_webhook"),
            '{"foo":"bar"}',
            content_type="application/json",
            HTTP_X_SQUARE_HMACSHA256_SIGNATURE=self.SHA256_SIGNATURE,
        )

        self.assertTrue(response.status_code, 400)
        self.assertIn(b"Missing event_id", response.content)

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_square_webhook_idempotency(self, mock_build_absolute_uri):
        notification = PaymentWebhookNotification(
            event_id=self.EVENT_ID, body=self.WEBHOOK_BODY, headers=dict()
        )
        notification.save()

        mock_build_absolute_uri.return_value = self.NOTIFICATION_URL

        response = self.client.post(
            reverse("registration:square_webhook"),
            self.WEBHOOK_BODY,
            content_type="application/json",
            HTTP_X_SQUARE_HMACSHA256_SIGNATURE=self.SHA256_SIGNATURE,
        )

        self.assertTrue(response.status_code, 409)
