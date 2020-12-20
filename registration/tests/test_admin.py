import json
import time
import uuid

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from registration import admin, payments
from registration.admin import OrderAdmin
from registration.models import *
from registration.tests.common import *


class TestOrderAdmin(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.admin_user.save()
        self.normal_user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "john"
        )
        self.normal_user.staff_member = True
        self.normal_user.save()

        # Create a Square order to test against:
        self.cash_order = Order(
            total=100,
            billingType=Order.CASH,
            status=Order.COMPLETED,
            reference="CASH_ORDER_1",
        )
        self.credit_order = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="CREDIT_ORDER_1",
        )
        self.comped_order = Order(
            total=100,
            billingType=Order.COMP,
            status=Order.COMPLETED,
            reference="COMPED_ORDER_1",
        )
        self.unpaid_order = Order(
            total=100,
            billingType=Order.UNPAID,
            status=Order.COMPLETED,
            reference="UNPAID_ORDER_1",
        )
        self.failed_order = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.FAILED,
            reference="FAILED_ORDER_1",
        )

        self.square_order = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="SQUARE_ORDER_1",
        )
        self.square_order.apiData = """
        {
            "payment": {
                "amount_money": {
                    "amount": 10000,
                    "currency": "USD"
                },
                "billing_address": {
                    "address_line_1": "Qui qui quasi amet ",
                    "address_line_2": "Sunt voluptas dolori",
                    "administrative_district_level_1": "",
                    "country": "FK",
                    "locality": "Quam earum Nam dolor",
                    "postal_code": "13271"
                },
                "card_details": {
                    "avs_status": "AVS_ACCEPTED",
                    "card": {
                        "bin": "411111",
                        "card_brand": "VISA",
                        "exp_month": 2,
                        "exp_year": 2021,
                        "fingerprint": "sq-1-DjCOZOf2iusD6RSZ3k7XEjS0rxZB24OMDtlav-NIIWmZazJHNYRRw8iK3DFQFSOfgA",
                        "last_4": "1111"
                    },
                    "cvv_status": "CVV_ACCEPTED",
                    "entry_method": "KEYED",
                    "statement_description": "SQ *DEFAULT TEST ACCOUNT",
                    "status": "CAPTURED"
                },
                "created_at": "2020-02-05T01:40:30.145Z",
                "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                "location_id": "MESD3N22DWR0F",
                "order_id": "WsfpRocSvcmpVJn6CmkkoTVrOhMZY",
                "processing_fee": [
                    {
                        "amount_money": {
                            "amount": 190,
                            "currency": "USD"
                        },
                        "effective_at": "2020-02-05T03:40:31.000Z",
                        "type": "INITIAL"
                    }
                ],
                "receipt_number": "bxMr",
                "receipt_url": "https://squareup.com/receipt/preview/bxMrD6jppRDNzVIDeou2qd24MCOZY",
                "reference_id": "SQUARE_ORDER_1",
                "refund_ids": [
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_fLgRWXBS4HCzA8bsHUwSOGPtQfFL5DHNYo0sJJ7HZNM",
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_ELsVHdtGxFzZxvBNr7MgWWReFNNvxV1DyZwH6IVnccG",
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_LXmYcw4D8qdrGjQGpL0Iy0XuFSKfEzpNXgfgzfm49TJ",
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_sqoyKz6Dz4PADiP8IemxSaHaNJg0lL8qDU3BBu4ojxF",
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_COroghYTDynfpIFO6RwXIP1sUxWa7eobswR1GOvYx1F"
                ],
                "refunded_money": {
                    "amount": 4700,
                    "currency": "USD"
                },
                "source_type": "CARD",
                "status": "COMPLETED",
                "total_money": {
                    "amount": 5500,
                    "currency": "USD"
                },
                "updated_at": "2020-02-06T11:28:31.883Z"
            },
            "refunds": [
                {
                    "amount_money": {
                        "amount": 1000,
                        "currency": "USD"
                    },
                    "created_at": "2020-02-06T10:59:34.855Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_ELsVHdtGxFzZxvBNr7MgWWReFNNvxV1DyZwH6IVnccG",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "8dUqeTvb3B6Bvphs9w5kLumZnJaZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "processing_fee": [
                        {
                            "amount_money": {
                                "amount": -29,
                                "currency": "USD"
                            },
                            "effective_at": "2020-02-05T03:40:31.000Z",
                            "type": "INITIAL"
                        }
                    ],
                    "reason": "testing second $10 refund",
                    "status": "COMPLETED",
                    "updated_at": "2020-02-06T10:59:38.223Z"
                },
                {
                    "amount_money": {
                        "amount": 500,
                        "currency": "USD"
                    },
                    "created_at": "2020-02-06T11:25:09.726Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_sqoyKz6Dz4PADiP8IemxSaHaNJg0lL8qDU3BBu4ojxF",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "EXBbGNCQlPUL5zbTlCOf56OspvJZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "reason": " [rechner]",
                    "status": "PENDING",
                    "updated_at": "2020-02-06T11:25:09.726Z"
                },
                {
                    "amount_money": {
                        "amount": 200,
                        "currency": "USD"
                    },
                    "created_at": "2020-02-06T11:28:31.883Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_COroghYTDynfpIFO6RwXIP1sUxWa7eobswR1GOvYx1F",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "e8Rnf1oG5Ruiv6CG0uTXksvvWhcZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "reason": "Test $2 refund [rechner]",
                    "status": "PENDING",
                    "updated_at": "2020-02-06T11:28:31.883Z"
                }
            ]
        }
        """
        self.square_order.save()

        self.square_order_bad_id = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="SQUARE_ORDER_1",
        )
        self.square_order_bad_id.apiData = '{"payment" : { "id" : "bad-payment-id" }}'
        self.square_order_bad_id.save()

        self.cash_order.save()
        self.credit_order.save()
        self.comped_order.save()
        self.failed_order.save()
        self.unpaid_order.save()

    def test_save_model(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="john", password="john"))
        # Shouldn't be able to save if order type is changed to REFUND or REFUND_PENDING
        form_data = {
            "status": Order.REFUNDED,
        }
        response = self.client.post(
            reverse("admin:order_refund", args=(self.cash_order.id,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You do not have permission to issue refunds.")
        order = Order.objects.get(id=self.cash_order.id)
        self.assertEqual(order.status, Order.COMPLETED)

    def test_refund_view_access_denied(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="john", password="john"))
        response = self.client.get(
            reverse("admin:order_refund", args=(self.cash_order.id,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access denied")

    def test_refund_view(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("admin:registration_order_change", args=(self.cash_order.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Access denied")
        self.assertNotContains(response, "Square data")

        response = self.client.get(
            reverse("admin:registration_order_change", args=(self.square_order.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Square data")

    def test_refund_view_post_access_denied(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="john", password="john"))
        form_data = {
            "amount": "10.00",
            "reason": "test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(self.cash_order.id,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access denied")

    def test_refund_view_invalid_refund(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        form_data = {
            "amount": "150.00",
            "reason": "test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(self.cash_order.id,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot exceed order total")
        self.assertEqual(self.cash_order.total, 100)
        self.assertEqual(self.cash_order.status, Order.COMPLETED)

        form_data = {
            "amount": "-50.00",
            "reason": "test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        response = self.client.post(
            reverse("admin:order_refund", args=(self.cash_order.id,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid form data")
        self.assertEqual(self.cash_order.total, 100)
        self.assertEqual(self.cash_order.status, Order.COMPLETED)

    def test_full_cash_refund(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))

        form_data = {
            "amount": self.cash_order.total,
            "reason": "Full cash refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)

        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(self.cash_order.id,)),
            form_data,
            follow=True,
        )

        order = Order.objects.get(id=self.cash_order.id)
        self.assertEqual(order.total, 0)
        self.assertEqual(order.status, Order.REFUNDED)

    def test_partial_cash_refund(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))

        form_data = {
            "amount": "50.00",
            "reason": "Partial cash refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)

        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(self.cash_order.id,)),
            form_data,
            follow=True,
        )

        order = Order.objects.get(id=self.cash_order.id)
        self.assertEqual(order.total, 50)
        self.assertEqual(order.status, Order.REFUNDED)

    def test_refund_comped_and_failed(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        form_data = {
            "amount": self.comped_order.total,
            "reason": "comped and failed test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(self.comped_order.id,)),
            form_data,
            follow=True,
        )
        self.assertContains(response, "Comped orders cannot be refunded")

        response = self.client.post(
            reverse("admin:order_refund", args=(self.failed_order.id,)),
            form_data,
            follow=True,
        )
        self.assertContains(response, "Failed orders cannot be refunded")

        response = self.client.post(
            reverse("admin:order_refund", args=(self.unpaid_order.id,)),
            form_data,
            follow=True,
        )
        self.assertContains(response, "Unpaid orders cannot be refunded")

    def create_square_order(self, nonce="cnon:card-nonce-ok", autocomplete=True):
        order = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="SQUARE_ORDER_2",
            lastFour="1111",
        )
        body = {
            "idempotency_key": str(uuid.uuid4()),
            "source_id": nonce,
            "autocomplete": autocomplete,
            "amount_money": {"amount": 10000, "currency": settings.SQUARE_CURRENCY,},
            "reference_id": order.reference,
            "billing_address": {"postal_code": "94042",},
            "location_id": settings.SQUARE_LOCATION_ID,
        }
        square_response = payments.payments_api.create_payment(body)
        order.apiData = json.dumps(square_response.body)
        order.save()
        if nonce == "cnon:card-nonce-ok":
            self.assertTrue(square_response.is_success())
        time.sleep(2)
        return order

    def test_square_refund(self):
        order = self.create_square_order()

        self.assertTrue(self.client.login(username="admin", password="admin"))
        form_data = {
            "amount": order.total,
            "reason": "full refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)

        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )

        order = Order.objects.get(id=order.id)
        self.refunded_square_order = order
        self.assertEqual(order.total, 0)
        self.assertEqual(order.status, Order.REFUND_PENDING)

    def test_partial_refund(self):
        order = self.create_square_order()
        order.orgDonation = 20
        order.charityDonation = 20
        order.save()

        self.assertTrue(self.client.login(username="admin", password="admin"))
        form_data = {
            "amount": "25",
            "reason": "1st $25 refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )

        order = Order.objects.get(id=order.id)
        self.refunded_square_order = order
        self.assertEqual(order.total, 75)
        self.assertEqual(order.charityDonation, 20)
        self.assertEqual(order.orgDonation, 20)
        self.assertEqual(order.status, Order.REFUND_PENDING)

        form_data = {
            "amount": "50",
            "reason": "2nd $50 refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )
        order = Order.objects.get(id=order.id)
        self.assertContains(
            response,
            "Refunded order has caused charity and organization donation amounts to reset.",
        )
        self.refunded_square_order = order
        self.assertEqual(order.total, 25)
        self.assertEqual(order.charityDonation, 25)
        self.assertEqual(order.orgDonation, 0)
        self.assertEqual(order.status, Order.REFUND_PENDING)

    def test_refresh_view(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("admin:order_refresh", args=(self.credit_order.id,)), follow=True
        )
        self.assertRedirects(
            response,
            reverse("admin:registration_order_change", args=(self.credit_order.id,)),
        )
        self.assertContains(
            response, "Error while loading JSON from apiData field for this order",
        )

        # Test with bad square ID:
        response = self.client.get(
            reverse("admin:order_refresh", args=(self.square_order_bad_id.id,)),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "admin:registration_order_change", args=(self.square_order_bad_id.id,)
            ),
        )
        self.assertContains(
            response, "INVALID_REQUEST_ERROR - NOT_FOUND",
        )
        self.assertContains(response, "There was a problem")

        # Test against captured & failed transactions:
        order = self.create_square_order(nonce="cnon:card-nonce-declined")
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse("admin:registration_order_change", args=(order.id,)),
        )
        order = Order.objects.get(id=order.id)
        self.assertEqual(order.status, order.FAILED)

        order = self.create_square_order(autocomplete=False)
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse("admin:registration_order_change", args=(order.id,)),
        )
        order = Order.objects.get(id=order.id)
        self.assertEqual(order.status, order.CAPTURED)

        # Create refund to test admin form data against:
        order = self.create_square_order()
        form_data = {
            "amount": order.total,
            "reason": "full refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)

        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )

        order = Order.objects.get(id=order.id)
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse("admin:registration_order_change", args=(order.id,)),
        )
        self.assertContains(
            response, "Refreshed order information from Square successfully"
        )
        self.assertContains(response, "Square data")
        self.assertContains(response, "$100")
        self.assertContains(response, "-$100")
        self.assertContains(response, "full refund test [admin]")


class TestCashDrawerAdmin(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.admin_user.save()

    def test_save_model(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        form_data = {
            "tendered": "",
            "total": 0,
            "action": Cashdrawer.TRANSACTION,
        }

        response = self.client.post(
            reverse("admin:registration_cashdrawer_add"), form_data, follow=True
        )
        cash_drawer = Cashdrawer.objects.get(id=1)
        self.assertEqual(cash_drawer.tendered, 0)
        self.assertEqual(cash_drawer.user, self.admin_user)
        cash_drawer.delete()


class TestTwoFactorAdmin(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user("john", "lennon@thebeatles.com", "john")
        self.user_2 = User.objects.create_superuser("admin", "admin@host", "admin")
        self.user_1.staff_member = True
        self.user_1.save()
        self.user_2.save()

    def test_disable_two_factor(self):
        query_set = [self.user_1, self.user_2]
        admin.disable_two_factor(None, None, query_set)
