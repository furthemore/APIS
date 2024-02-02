import json

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch

from registration.models import (
    Attendee,
    Badge,
    BanList,
    Event,
    Order,
    OrderItem,
    PaymentWebhookNotification,
)
from registration.tests.common import DEFAULT_EVENT_ARGS, TEST_ATTENDEE_ARGS


class TestSquareRefundWebhooks(TestCase):
    EVENT_ID = "9c7300fc-5b0d-3ffb-8cd0-c2987b21099c"
    WEBHOOK_BODY = """{"merchant_id":"PXRNP8VV5DSQH","type":"refund.updated",
    "event_id":"9c7300fc-5b0d-3ffb-8cd0-c2987b21099c","created_at":"2022-12-29T06:30:29.411Z",
    "data":{"type":"refund","id":"HH2sTvwhwFGq0Ivi4uBRvFJt55ZZY_rui4h8ypOw5yihLEBc5UC2HqJS0xUl7gukSQ7lq1AuF",
    "object":{"refund":{"amount_money":{"amount":9000,"currency":"USD"},"created_at":"2022-12-29T06:30:27.642Z",
    "destination_type":"CARD","id":"HH2sTvwhwFGq0Ivi4uBRvFJt55ZZY_rui4h8ypOw5yihLEBc5UC2HqJS0xUl7gukSQ7lq1AuF",
    "location_id":"MESD3N22DWR0F","order_id":"gzamDxDtniM1nKbkDYZHYH0xbEOZY",
    "payment_id":"HH2sTvwhwFGq0Ivi4uBRvFJt55ZZY","reason":" [rechner]","status":"COMPLETED",
    "updated_at":"2022-12-29T06:30:29.404Z","version":6}}}}"""
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
        self.assertEqual(webhook.event_type, webhook.body["type"])

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


class TestSquareDisputeWebhookCreate(TestCase):
    # It's possible to test this E2E against the disputes API sandbox by setting particular payment values
    # https://developer.squareup.com/docs/disputes-api/sandbox-testing
    EVENT_ID = "936b73e0-5827-3a6f-a162-427b04a89d43"
    PAYMENT_BODY = {
        "payment": {
            "id": "HbuhSBp9yJpt9iapF0ukqVvkCDMZY",
            "created_at": "2024-02-02T01:46:48.469Z",
            "updated_at": "2024-02-02T01:46:48.774Z",
            "amount_money": {"amount": 8804, "currency": "USD"},
            "status": "COMPLETED",
            "delay_duration": "PT168H",
            "source_type": "CARD",
            "card_details": {
                "status": "CAPTURED",
                "card": {
                    "card_brand": "VISA",
                    "last_4": "1111",
                    "exp_month": 5,
                    "exp_year": 2025,
                    "fingerprint": "sq-1-DjCOZOf2iusD6RSZ3k7XEjS0rxZB24OMDtlav-NIIWmZazJHNYRRw8iK3DFQFSOfgA",
                    "card_type": "CREDIT",
                    "prepaid_type": "NOT_PREPAID",
                    "bin": "411111",
                },
                "entry_method": "KEYED",
                "cvv_status": "CVV_ACCEPTED",
                "avs_status": "AVS_ACCEPTED",
                "statement_description": "SQ *DEFAULT TEST ACCOUNT",
                "card_payment_timeline": {
                    "authorized_at": "2024-02-02T01:46:48.589Z",
                    "captured_at": "2024-02-02T01:46:48.774Z",
                },
            },
            "location_id": "MESD3N22DWR0F",
            "order_id": "myU3LuxKN4de1sjezcKrStcAa0FZY",
            "reference_id": "GJWENL",
            "risk_evaluation": {
                "created_at": "2024-02-02T01:46:48.589Z",
                "risk_level": "NORMAL",
            },
            "billing_address": {
                "address_line_1": "Sint reprehenderit",
                "address_line_2": "Veritatis accusamus ",
                "locality": "Nisi obcaecati et er",
                "administrative_district_level_1": "",
                "postal_code": "11111",
                "country": "AZ",
                "first_name": "Chancellor",
                "last_name": "Austin",
            },
            "total_money": {"amount": 8804, "currency": "USD"},
            "approved_money": {"amount": 8804, "currency": "USD"},
            "receipt_number": "Hbuh",
            "receipt_url": "https://squareupsandbox.com/receipt/preview/HbuhSBp9yJpt9iapF0ukqVvkCDMZY",
            "delay_action": "CANCEL",
            "delayed_until": "2024-02-09T01:46:48.469Z",
            "application_details": {
                "square_product": "ECOMMERCE_API",
                "application_id": "sandbox-sq0idb-GRQ64U8t_7bH0aJ51bQykw",
            },
            "version_token": "vSfY8mYPsyOVaNPqtPXomLQkZnqpkOx3yol16moTfGV6o",
        }
    }
    WEBHOOK_BODY = json.loads(
        """{
      "merchant_id": "PXRNP8VV5DSQH",
      "location_id": "MESD3N22DWR0F",
      "type": "dispute.created",
      "event_id": "936b73e0-5827-3a6f-a162-427b04a89d43",
      "created_at": "2024-02-02T01:46:52.549Z",
      "data": {
        "type": "dispute",
        "id": "7uVMgYjRu0KNYP1Dx8GRlD",
        "object": {
          "dispute": {
            "amount_money": {
              "amount": 8804,
              "currency": "USD"
            },
            "brand_dispute_id": "iS7RtlifSQiWt1WQ2npk9Q",
            "card_brand": "VISA",
            "created_at": "2024-02-02T01:46:52.549Z",
            "disputed_payment": {
              "payment_id": "HbuhSBp9yJpt9iapF0ukqVvkCDMZY"
            },
            "due_at": "2024-02-16T00:00:00.000Z",
            "id": "7uVMgYjRu0KNYP1Dx8GRlD",
            "location_id": "MESD3N22DWR0F",
            "reason": "NO_KNOWLEDGE",
            "reported_at": "2024-02-02T00:00:00.000Z",
            "state": "EVIDENCE_REQUIRED",
            "updated_at": "2024-02-02T01:46:52.549Z"
          }
        }
      }
    }"""
    )
    SHA256_SIGNATURE = "thkLhRk6xWbmuN0N0alo56Dcl1U="
    SIGNATURE_KEY = "Op83IrwJoz1do9FKFYE71g"
    NOTIFICATION_URL = "https://webhook.site/4834cace-d117-4214-af36-5e8df062133d"

    def setUp(self) -> None:
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()
        self.order = Order(
            total="88.04",
            status=Order.COMPLETED,
            reference="FOOBAR",
            billingEmail="apis@mailinator.com",
            lastFour="1111",
            apiData=self.PAYMENT_BODY,
        )
        self.order.save()
        self.attendee = Attendee(**TEST_ATTENDEE_ARGS)
        self.attendee.save()
        self.badge = Badge(
            attendee=self.attendee, event=self.event, badgeName="Banned 4 Lyfe"
        )
        self.badge.save()
        self.order_item = OrderItem(
            order=self.order, badge=self.badge, enteredBy="Test"
        )
        self.order_item.save()
        self.order.refresh_from_db()

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_dispute_webhook(self, mock_build_absolute_uri):
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
        self.assertEqual(webhook.event_type, webhook.body["type"])

        # Test that API data of the existing order has expected new content from the webhook:
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.apiData["dispute"],
            self.WEBHOOK_BODY["data"]["object"]["dispute"],
        )

        self.order.refresh_from_db()
        ban_list = BanList.objects.filter(email=self.attendee.email).first()
        self.assertEqual(self.attendee.firstName, ban_list.firstName)
        self.assertEqual(self.attendee.lastName, ban_list.lastName)

    @override_settings(SQUARE_WEBHOOK_SIGNATURE_KEY=SIGNATURE_KEY)
    @patch("django.http.request.HttpRequest.build_absolute_uri")
    def test_dispute_payment_id_not_found(self, mock_build_absolute_uri):
        self.order.apiData = {}
        self.order.save()
        self.order.refresh_from_db()

        mock_build_absolute_uri.return_value = self.NOTIFICATION_URL

        response = self.client.post(
            reverse("registration:square_webhook"),
            self.WEBHOOK_BODY,
            content_type="application/json",
            HTTP_X_SQUARE_HMACSHA256_SIGNATURE=self.SHA256_SIGNATURE,
        )

        self.assertTrue(response.status_code, 200)
        webhook = PaymentWebhookNotification.objects.get(event_id=self.EVENT_ID)
        self.assertFalse(webhook.processed)
