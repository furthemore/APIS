import time
import uuid
from typing import List
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase, tag
from django.urls import reverse
from square.core.api_error import ApiError
from square.requests.address import AddressParams
from square.requests.money import MoneyParams

from registration import admin, payments
from registration.admin import OrderAdmin
from registration.models import *
from registration.templatetags import site as site_tags
from registration.tests.common import *


class TestOrderAdmin(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@host", "admin"
        )  # NOSONAR
        self.admin_user.save()
        self.normal_user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "john"  # NOSONAR
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
        self.square_order.apiData = {
            "payment": {
                "amount_money": {"amount": 10000, "currency": "USD"},
                "billing_address": {
                    "address_line_1": "Qui qui quasi amet ",
                    "address_line_2": "Sunt voluptas dolori",
                    "administrative_district_level_1": "",
                    "country": "FK",
                    "locality": "Quam earum Nam dolor",
                    "postal_code": "13271",
                },
                "card_details": {
                    "avs_status": "AVS_ACCEPTED",
                    "card": {
                        "bin": "411111",
                        "card_brand": "VISA",
                        "exp_month": 2,
                        "exp_year": 2021,
                        "fingerprint": "sq-1-DjCOZOf2iusD6RSZ3k7XEjS0rxZB24OMDtlav-NIIWmZazJHNYRRw8iK3DFQFSOfgA",
                        "last_4": "1111",
                    },
                    "cvv_status": "CVV_ACCEPTED",
                    "entry_method": "KEYED",
                    "statement_description": "SQ *DEFAULT TEST ACCOUNT",
                    "status": "CAPTURED",
                },
                "created_at": "2020-02-05T01:40:30.145Z",
                "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                "location_id": "MESD3N22DWR0F",
                "order_id": "WsfpRocSvcmpVJn6CmkkoTVrOhMZY",
                "processing_fee": [
                    {
                        "amount_money": {"amount": 190, "currency": "USD"},
                        "effective_at": "2020-02-05T03:40:31.000Z",
                        "type": "INITIAL",
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
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_COroghYTDynfpIFO6RwXIP1sUxWa7eobswR1GOvYx1F",
                ],
                "refunded_money": {"amount": 4700, "currency": "USD"},
                "source_type": "CARD",
                "status": "COMPLETED",
                "total_money": {"amount": 5500, "currency": "USD"},
                "updated_at": "2020-02-06T11:28:31.883Z",
            },
            "refunds": [
                {
                    "amount_money": {"amount": 1000, "currency": "USD"},
                    "created_at": "2020-02-06T10:59:34.855Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_ELsVHdtGxFzZxvBNr7MgWWReFNNvxV1DyZwH6IVnccG",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "8dUqeTvb3B6Bvphs9w5kLumZnJaZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "processing_fee": [
                        {
                            "amount_money": {"amount": -29, "currency": "USD"},
                            "effective_at": "2020-02-05T03:40:31.000Z",
                            "type": "INITIAL",
                        }
                    ],
                    "reason": "testing second $10 refund",
                    "status": "COMPLETED",
                    "updated_at": "2020-02-06T10:59:38.223Z",
                },
                {
                    "amount_money": {"amount": 500, "currency": "USD"},
                    "created_at": "2020-02-06T11:25:09.726Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_sqoyKz6Dz4PADiP8IemxSaHaNJg0lL8qDU3BBu4ojxF",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "EXBbGNCQlPUL5zbTlCOf56OspvJZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "reason": " [rechner]",
                    "status": "PENDING",
                    "updated_at": "2020-02-06T11:25:09.726Z",
                },
                {
                    "amount_money": {"amount": 200, "currency": "USD"},
                    "created_at": "2020-02-06T11:28:31.883Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_COroghYTDynfpIFO6RwXIP1sUxWa7eobswR1GOvYx1F",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "e8Rnf1oG5Ruiv6CG0uTXksvvWhcZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "reason": "Test $2 refund [rechner]",
                    "status": "PENDING",
                    "updated_at": "2020-02-06T11:28:31.883Z",
                },
            ],
        }
        self.square_order.save()

        self.square_order_bad_id = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="SQUARE_ORDER_1",
        )
        self.square_order_bad_id.apiData = {"payment": {"id": "bad-payment-id"}}
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
        self.assertNotContains(response, "Square Data")

        response = self.client.get(
            reverse("admin:registration_order_change", args=(self.square_order.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Square Data")

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

    @tag("square")
    def create_square_order(self, nonce="cnon:card-nonce-ok", autocomplete=True):
        order = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="SQUARE_ORDER_2",
            lastFour="1111",
        )
        try:
            square_response = payments.client.payments.create(
                idempotency_key=str(uuid.uuid4()),
                source_id=nonce,
                autocomplete=autocomplete,
                amount_money=MoneyParams(
                    amount=10000, currency=settings.SQUARE_CURRENCY
                ),
                reference_id=order.reference,
                billing_address=AddressParams(postal_code="94042"),
                location_id=settings.SQUARE_LOCATION_ID,
            )
            time.sleep(2)
            order.apiData = square_response.model_dump()
        except ApiError as e:
            square_response = e
            order.apiData = e.body
        order.save()
        if nonce == "cnon:card-nonce-ok":
            self.assertEqual(square_response.errors, None)
        return order

    @tag("square")
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
            reverse("admin:order_refund", args=(order.id,)),
            form_data,
            follow=True,
        )

        order = Order.objects.get(id=order.id)
        self.refunded_square_order = order
        self.assertEqual(order.total, 0)
        self.assertEqual(order.status, Order.REFUND_PENDING)

    @tag("square")
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
            reverse("admin:order_refund", args=(order.id,)),
            form_data,
            follow=True,
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
            reverse("admin:order_refund", args=(order.id,)),
            form_data,
            follow=True,
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

    @tag("square")
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
            response,
            "Error while loading JSON from apiData field for this order",
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
            response,
            "INVALID_REQUEST_ERROR - NOT_FOUND",
        )
        self.assertContains(response, "There was a problem")

        # Test against captured & failed transactions:
        order = self.create_square_order(nonce="cnon:card-nonce-declined")
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response,
            reverse("admin:registration_order_change", args=(order.id,)),
        )
        order = Order.objects.get(id=order.id)
        self.assertEqual(order.status, order.FAILED)

        order = self.create_square_order(autocomplete=False)
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response,
            reverse("admin:registration_order_change", args=(order.id,)),
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
            reverse("admin:order_refund", args=(order.id,)),
            form_data,
            follow=True,
        )

        order = Order.objects.get(id=order.id)
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response,
            reverse("admin:registration_order_change", args=(order.id,)),
        )
        self.assertContains(
            response, "Refreshed order information from Square successfully"
        )
        self.assertContains(response, "Square Data")
        self.assertContains(response, "$100")
        self.assertContains(response, "-$100")
        self.assertContains(response, "full refund test [admin]")


class TestCashDrawerAdmin(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@host", "admin"
        )  # NOSONAR
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


class TestOrderItemAdmin(OrdersTestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@host", "admin"
        )  # NOSONAR
        self.admin_user.save()
        self.order = Order(total="90.00", reference="FOOBAR")
        self.order.save()
        attendee = Attendee(**TEST_ATTENDEE_ARGS)
        attendee.save()
        self.badge = Badge(event=self.event, attendee=attendee)
        self.badge.save()
        self.order_item = OrderItem(
            order=self.order, badge=self.badge, priceLevel=self.price_90
        )
        self.order_item.save()

    def test_save_model(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.assertNotEqual(self.order_item.enteredBy, "admin")

        form_data = {
            "order": self.order.pk,
            "badge": self.badge.pk,
            "priceLevel": self.price_90.pk,
        }

        response = self.client.post(
            reverse("admin:registration_orderitem_change", args=(self.order_item.pk,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.enteredBy, "admin")


class AdminTestCase(TestCase):
    def setUp(self):
        self.admin_site = AdminSite()
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()


class TestDealerAdmin(AdminTestCase):
    def setUp(self):
        super().setUp()
        self.dealer_admin = admin.DealerAdmin(model=Dealer, admin_site=self.admin_site)
        self.attendee = Attendee(**TEST_ATTENDEE_ARGS)
        self.attendee.save()
        self.dealer = Dealer(
            attendee=self.attendee, businessName="Test business", approved=True
        )
        self.dealer.save()

    def test_get_email(self):
        self.assertEqual(self.dealer_admin.get_email(self.dealer), self.attendee.email)

    def test_get_email_no_attendee(self):
        dealer = Dealer(businessName="Whatever")
        self.assertEqual(self.dealer_admin.get_email(dealer), "--")


class TestDealerAsstAdmin(TestDealerAdmin):
    def setUp(self):
        super().setUp()
        self.asst_admin = admin.DealerAsstAdmin(
            model=DealerAsst, admin_site=AdminSite()
        )
        self.assistant = DealerAsst(
            dealer=self.dealer,
            name="Lovely Assistant",
            email="foo@bar.com",
            license="n/a",
        )

    def test_dealer_businessname(self):
        self.assertEqual(
            self.asst_admin.dealer_businessname(self.assistant),
            self.dealer.businessName,
        )

    def test_dealer_approved(self):
        self.assertEqual(
            self.asst_admin.dealer_approved(self.assistant), self.dealer.approved
        )

    def test_send_assistant_registration_email(self):
        pass

    def test_asst_registered(self):
        # Assign an attendee to our assistant to make this case work
        attendee = Attendee(**TEST_ATTENDEE_ARGS)
        attendee.save()
        self.assistant.attendee = attendee
        self.assertTrue(self.asst_admin.asst_registered(self.assistant))

    def test_asst_registered_no_attendee(self):
        # The assistant we set up doesn't have an attendee assigned yet:
        self.assertFalse(self.asst_admin.asst_registered(self.assistant))


class TestAssignBadgeNumbers(OrdersTestCase):
    def setUp(self):
        super().setUp()

        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()

    def _make_attendee(self, index: int) -> Attendee:
        args = TEST_ATTENDEE_ARGS.copy()
        args["email"] = f"badge-attendee-{index}@mailinator.org"
        attendee = Attendee(**args)
        attendee.save()
        return attendee

    @patch("django.contrib.messages.warning")
    def test_assignment_works(self, mock_messages_warning: Mock):
        badges: List[Badge] = []

        args = DEFAULT_EVENT_ARGS.copy()
        args["default"] = False
        other_event = Event(**args)
        other_event.save()

        badge = Badge(event=self.event, attendee=self._make_attendee(0))
        badge.save()
        badges.append(badge)

        order = Order(total="90.00", reference="FOOBAR")
        order.save()

        badge = Badge(event=other_event, attendee=self._make_attendee(1))
        badge.save()
        badges.append(badge)

        order_item = OrderItem(order=order, badge=badge, priceLevel=self.price_90)
        order_item.save()

        for i in range(5):
            order = Order(total="90.00", reference="FOOBAR")
            order.save()

            badge = Badge(event=self.event, attendee=self._make_attendee(i + 2))
            badge.save()
            badges.append(badge)

            order_item = OrderItem(order=order, badge=badge, priceLevel=self.price_90)
            order_item.save()

        for num in [3, 4]:
            ReservedBadgeNumbers(badgeNumber=num).save()

        admin.assign_badge_numbers(None, None, Badge.objects.all())
        self.assertEqual(mock_messages_warning.call_count, 2)

        EXPECTED = [None, None, 1, 2, 5, 6, 7]
        for idx, badge in enumerate(badges):
            badge.refresh_from_db()
            self.assertEqual(badge.badgeNumber, EXPECTED[idx])
