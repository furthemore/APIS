from django.test import TestCase, tag
from mock import patch

from registration import payments

TEST_ORDER_RESULT = {
    "orders": [
        {
            "id": "ynouXaif1NEotJYzdwBfakreV",
            "location_id": "MESD3N22DWR0F",
            "line_items": [
                {
                    "uid": "092d546f-165b-4037-863e-b998b734dd01",
                    "quantity": "1",
                    "base_price_money": {"amount": 100, "currency": "USD"},
                    "note": "note",
                    "gross_sales_money": {"amount": 100, "currency": "USD"},
                    "total_tax_money": {"amount": 0, "currency": "USD"},
                    "total_discount_money": {"amount": 0, "currency": "USD"},
                    "total_money": {"amount": 100, "currency": "USD"},
                    "variation_total_price_money": {"amount": 100, "currency": "USD"},
                }
            ],
            "created_at": "2020-02-25T07:26:41Z",
            "updated_at": "2020-02-25T07:26:41Z",
            "state": "COMPLETED",
            "total_tax_money": {"amount": 0, "currency": "USD"},
            "total_discount_money": {"amount": 0, "currency": "USD"},
            "total_tip_money": {"amount": 0, "currency": "USD"},
            "total_money": {"amount": 100, "currency": "USD"},
            "closed_at": "2020-02-25T07:26:41Z",
            "tenders": [
                {
                    "id": "7VceHkRWU2iFztahpbYt1AUCvaB",
                    "location_id": "MESD3N22DWR0F",
                    "transaction_id": "ynouXaif1NEotJYzdwBfakreV",
                    "created_at": "2020-02-25T07:26:39Z",
                    "amount_money": {"amount": 100, "currency": "USD"},
                    "processing_fee_money": {"amount": 13, "currency": "USD"},
                    "customer_id": "3E8T1J32960HD18W1ECXGEZ7HR",
                    "type": "CARD",
                    "card_details": {
                        "status": "CAPTURED",
                        "card": {
                            "card_brand": "VISA",
                            "last_4": "1218",
                            "fingerprint": "sq-1-1Oc-8ThrLQZ-xjmAdesWwDr1yVYnHVgWStPpjy3v8VedofgLU-N3oiie6jXLeSkK8Q",
                        },
                        "entry_method": "CONTACTLESS",
                    },
                }
            ],
            "total_service_charge_money": {"amount": 0, "currency": "USD"},
            "return_amounts": {
                "total_money": {"amount": 0, "currency": "USD"},
                "tax_money": {"amount": 0, "currency": "USD"},
                "discount_money": {"amount": 0, "currency": "USD"},
                "tip_money": {"amount": 0, "currency": "USD"},
                "service_charge_money": {"amount": 0, "currency": "USD"},
            },
            "net_amounts": {
                "total_money": {"amount": 100, "currency": "USD"},
                "tax_money": {"amount": 0, "currency": "USD"},
                "discount_money": {"amount": 0, "currency": "USD"},
                "tip_money": {"amount": 0, "currency": "USD"},
                "service_charge_money": {"amount": 0, "currency": "USD"},
            },
        }
    ]
}


class MockSquareResultSuccess(object):
    body = TEST_ORDER_RESULT
    errors = {}
    is_success = lambda x: True
    is_error = lambda x: False


class MockSquareResultFailure(object):
    body = {}
    errors = [
        {"category": "SOME_CATEGORY", "code": "E_FAIL", "detail": "Some extra message,"}
    ]
    is_success = lambda x: False
    is_error = lambda x: True


class TestSquareOrders(TestCase):
    @patch("registration.payments.orders_api.batch_retrieve_orders")
    def test_get_payments_from_order_id(self, mock_get_payments):
        mock_get_payments.return_value = MockSquareResultSuccess()
        result = payments.get_payments_from_order_id(
            TEST_ORDER_RESULT["orders"][0]["id"]
        )
        self.assertEqual(result, ["7VceHkRWU2iFztahpbYt1AUCvaB"])

    @patch("registration.payments.orders_api.batch_retrieve_orders")
    def test_get_payments_from_order_id_failure(self, mock_get_payments):
        mock_get_payments.return_value = MockSquareResultFailure()
        result = payments.get_payments_from_order_id(
            TEST_ORDER_RESULT["orders"][0]["id"]
        )
        self.assertIsNone(result)

    @tag("square")
    def test_get_payments_from_order_id_invalid(self):
        result = payments.get_payments_from_order_id("doesntexist")
        self.assertEqual(len(result), 0)
