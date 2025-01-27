import json
import time
import uuid
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpRequest
from django.test import Client, TestCase, tag
from django.urls import reverse

from registration import admin, payments
from registration.admin import OrderAdmin
from registration.models import *
from registration.templatetags import site as site_tags
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

    @tag("square")
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
            "amount_money": {
                "amount": 10000,
                "currency": settings.SQUARE_CURRENCY,
            },
            "reference_id": order.reference,
            "billing_address": {
                "postal_code": "94042",
            },
            "location_id": settings.SQUARE_LOCATION_ID,
        }
        square_response = payments.payments_api.create_payment(body)
        order.apiData = square_response.body
        order.save()
        if nonce == "cnon:card-nonce-ok":
            self.assertTrue(square_response.is_success())
        time.sleep(2)
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
        self.user_profile_admin = admin.UserProfileAdmin(
            model=User, admin_site=AdminSite()
        )
        self.user_1 = User.objects.create_user("john", "lennon@thebeatles.com", "john")
        self.user_2 = User.objects.create_superuser("admin", "admin@host", "admin")
        self.user_1.staff_member = True
        self.user_1.save()
        self.user_2.save()

    def test_two_factor_disabled(self):
        self.assertFalse(self.user_profile_admin.two_factor_enabled(self.user_1))

    def test_two_factor_enabled(self):
        self.user_2.u2f_keys.create(
            key_handle="bbavVvfXPz2w8S3IwIS0LkE1SkC3MQuXSYjAYHVPFqUJIRQTIEyM3D34Lv2G4a_PuAZkZIQ6XV3ocwp47cPYjg",
            public_key="BFp3EHDcpm5HxA4XYuCKlnNPZ3tphVzRvXsX2_J33REPU0bgFgWsUoyZHz6RGxdA84VgxDNI4lvUudr7JGmFdDk",
            app_id="http://localhost:8000",
        )
        self.assertTrue(self.user_profile_admin.two_factor_enabled(self.user_2))

    def test_disable_two_factor(self):
        query_set = [self.user_1, self.user_2]
        admin.disable_two_factor(None, None, query_set)


class TestOrderItemAdmin(OrdersTestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.admin_user.save()
        self.order = Order(total="90.00", reference="FOOBAR")
        self.order.save()
        self.badge = Badge(event=self.event)
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


class TestStaffAdmin(AdminTestCase):
    def setUp(self):
        super().setUp()
        event_args = dict(DEFAULT_EVENT_ARGS)
        event_args["name"] = "New Test Event"
        event_args["default"] = False
        self.new_event = Event(**event_args)
        self.new_event.save()
        self.staff_admin = admin.StaffAdmin(model=Staff, admin_site=self.admin_site)
        self.attendee = Attendee(**TEST_ATTENDEE_ARGS)
        self.attendee.save()
        self.badge = Badge(
            attendee=self.attendee, event=self.event, badgeName="DisStaff"
        )
        self.badge.save()
        self.staff = Staff(attendee=self.attendee, event=self.event)

    def test_checkin_staff(self):
        self.assertFalse(self.staff.checkedIn)
        admin.checkin_staff(None, None, [self.staff])
        self.assertTrue(self.staff.checkedIn)

    def test_send_staff_registration_email(self):
        admin.send_staff_registration_email(None, None, [self.staff])
        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

    def test_get_email(self):
        self.assertEqual(self.staff_admin.get_email(self.staff), self.attendee.email)

    def test_get_email_no_attendee(self):
        self.assertEqual(self.staff_admin.get_email(Staff()), "--")

    def test_get_badge(self):
        self.assertEqual(self.staff_admin.get_badge(self.staff), self.badge.badgeName)

    def test_get_badge_none(self):
        self.assertEqual(self.staff_admin.get_badge(Staff()), "--")

    def test_copy_to_event_form(self):
        request = HttpRequest()
        staff = Staff.objects.all()
        response = self.staff_admin.copy_to_event(request, staff)
        self.assertEqual(response.status_code, 200)

    @patch("registration.admin.StaffAdmin.message_user")
    def test_copy_to_event(self, mock_message_user):
        form_data = {
            "event": self.new_event.pk,
            "action": "copy_to_event",
            "_selected_action": "3",
        }
        request = HttpRequest()
        request.POST.update(form_data)

        response = self.staff_admin.copy_to_event(request, [self.staff])
        mock_message_user.assert_called_once()
        self.assertEqual(
            mock_message_user.call_args[0][1],
            f"Successfully copied 1 staff to {self.new_event.name}.",
        )
        self.assertEqual(Staff.objects.filter(event=self.new_event).count(), 1)
        Staff.objects.filter(event=self.new_event).delete()

    @patch("registration.admin.StaffAdmin.message_user")
    def test_copy_to_same_event(self, mock_message_user):
        form_data = {
            "event": self.event.pk,
            "action": "copy_to_event",
            "_selected_action": "3",
        }
        request = HttpRequest()
        request.POST.update(form_data)

        response = self.staff_admin.copy_to_event(request, [self.staff])
        mock_message_user.assert_called_once()
        self.assertEqual(
            mock_message_user.call_args[0][1],
            f"Successfully copied 0 staff to {self.event.name}.",
        )
        self.assertEqual(Staff.objects.filter(event=self.new_event).count(), 0)


class TestTempToken(TestCase):
    def setUp(self):
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()

        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.admin_user.save()

    @patch("registration.emails.send_email")
    def test_temp_token_send_email(self, mock_send_email):
        test_email_address = "test-admin@example.net"

        # Login to the admin section
        logged_in = self.client.login(username="admin", password="admin")
        self.assertTrue(logged_in)

        # Build out the create temp token form
        token = getRegistrationToken()
        form_data = {
            "token": token,
            "initial-token": token,
            "email": test_email_address,
            "ignore_time_window": "on",
            "validUntil_0": "2025-01-27",
            "validUntil_1": "00:00:00",
            "usedDate_0": "",
            "usedDate_1": "",
            "_save": "Save",
        }

        # Get the CSRF token from the form so we can POST properly
        response = self.client.get(
            reverse("admin:registration_temptoken_add")
        )
        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.find("form", id="temptoken_form")
        csrfmiddlewaretoken = form.find("input", attrs={"name": "csrfmiddlewaretoken"})
        form_data["csrfmiddlewaretoken"] = csrfmiddlewaretoken.attrs["value"]

        # Create the temp token
        response = self.client.post(
            reverse("admin:registration_temptoken_add"),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, "html.parser")

        # Make sure we weren't sent back to the create form
        form = soup.find("form", id="temptoken_form")
        self.assertIsNone(form)

        # Get the response message
        content = soup.find("div", attrs={"class": "content"})
        message = content.find("ul", attrs={"class": "messagelist"}).text.strip()
        # Standardize quotes
        message = message.replace('“', '"').replace('”', '"')
        expected_message = f'The temp token "{token}" was added successfully.'
        self.assertEqual(message, expected_message)

        # Build out the send staff token email form
        form_data = {
            "action": "send_staff_token_email",
            "select_across": "0",
            "index": "0",
            "_selected_action": "1",
        }

        # Get the CSRF token from the form so we can POST properly
        response = self.client.get(
            reverse("admin:registration_temptoken_changelist")
        )
        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.find("form", id="changelist-form")
        csrfmiddlewaretoken = form.find("input", attrs={"name": "csrfmiddlewaretoken"})
        form_data["csrfmiddlewaretoken"] = csrfmiddlewaretoken.attrs["value"]

        # Send the email
        response = self.client.post(
            reverse("admin:registration_temptoken_changelist"),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, "html.parser")
        # Get the response message
        content = soup.find("div", attrs={"class": "content"})
        message = content.find("ul", attrs={"class": "messagelist"}).text.strip()
        expected_message = f"Successfully sent email to {test_email_address}"
        self.assertEqual(message, expected_message)

        # Make sure the email was sent correctly
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]

        # Make sure the recipients are correct
        self.assertEqual(recipients, [test_email_address])

        # Make sure the correct endpoint was rendered
        expected_path = reverse("registration:new_staff", args=(token,))
        expected_fixed_path = f"/registration/newstaff/{token}"
        self.assertEqual(expected_path, expected_fixed_path)

        # Make sure the correct URL was rendered
        current_domain = site_tags.current_domain()
        expected_url = f"https://{current_domain}{expected_path}"
        self.assertIn(expected_url, plain_text)

        # Make sure the URL is correct in the HTML email
        expected_html_link = f"<a href='{expected_url}'>{expected_url}</a>"
        self.assertIn(expected_html_link, html_text)
