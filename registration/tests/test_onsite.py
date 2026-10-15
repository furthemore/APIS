import uuid
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.test.utils import override_settings

from registration.models import *
from registration.tests.common import *
from registration.views import onsite_admin


class OnsiteBaseTestCase(TestCase):
    def setUp(self):
        # Create some users
        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.normal_user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "john"
        )
        self.normal_user.staff_member = False
        self.normal_user.save()

        # Create some test terminals to push notifications to
        self.terminal = Firebase.objects.create(
            token="test", name="Terminal 1", web_access=True
        )

        # At least one event always mandatory
        self.event = Event.objects.create(**DEFAULT_EVENT_ARGS)

        self.price_45 = PriceLevel.objects.create(
            name="Attendee",
            description="Some test description here",
            basePrice=45.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )
        self.price_90 = PriceLevel.objects.create(
            name="Sponsor",
            description="Woot!",
            basePrice=90.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )

        self.option_conbook = PriceLevelOption.objects.create(
            optionName="Conbook", optionPrice=0.00, optionExtraType="bool"
        )
        self.option_shirt = PriceLevelOption.objects.create(
            optionName="Shirt Size", optionPrice=20.00, optionExtraType="ShirtSizes"
        )
        self.option_100_int = PriceLevelOption.objects.create(
            optionName="Something Pricy", optionPrice=100.00, optionExtraType="int"
        )

        self.price_45.priceLevelOptions.set(
            [self.option_conbook, self.option_shirt, self.option_100_int]
        )
        self.price_90.priceLevelOptions.set(
            [self.option_conbook, self.option_shirt, self.option_100_int]
        )

        self.shirt1 = ShirtSizes.objects.create(name="Test_Large")

        self.boogeyman_hold = HoldType.objects.create(name="Boogeyman")

        self.client = Client()

    def add_to_cart(
        self,
        level,
        options,
        *,
        email="apis@mailinator.com",
        first_name="Cameron",
        last_name="Christian",
        badge_name="Onsite Badge 1",
    ):
        form_data = {
            "attendee": {
                "address1": "Voluptas dolor dicta",
                "address2": "Debitis deleniti und",
                "asl": "",
                "badgeName": badge_name,
                "birthdate": "1989-02-07",
                "city": "64133",
                "country": "SK",
                "email": email,
                "emailsOk": False,
                "firstName": first_name,
                "lastName": last_name,
                "onsite": True,
                "phone": "+1 (143) 117-2402",
                "postal": "17416",
                "state": "KO",
                "surveyOk": False,
                "volDepts": "",
            },
            "event": self.event.name,
            "priceLevel": {"id": str(level.id), "options": options},
        }

        response = self.client.post(
            reverse("registration:add_to_cart"),
            json.dumps(form_data),
            content_type="application/json",
        )
        logging.info(response.content)
        self.assertEqual(response.status_code, 200)

    def stage_order(
        self,
        *,
        email="apis@mailinator.com",
        first_name="Cameron",
        badge_name="Onsite Badge 1",
    ) -> int:
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(
            self.price_45,
            options,
            email=email,
            first_name=first_name,
            badge_name=badge_name,
        )
        self.checkout()
        badge = Badge.objects.filter(attendee__email=email).order_by("id").last()
        return badge.id

    def checkout(self, charity_donation="0.00", org_donation="0.00"):
        post_data = {
            "billingData": {},
            "charityDonation": charity_donation,
            "onsite": True,
            "orgDonation": org_donation,
        }

        response = self.client.post(
            reverse("registration:checkout"),
            json.dumps(post_data),
            content_type="application/json",
            headers={"idempotency-key": str(uuid.uuid4())},
        )

        return response


class TestOnsiteCart(OnsiteBaseTestCase):
    def setUp(self):
        super(TestOnsiteCart, self).setUp()

    def test_onsite_open(self):
        self.event.onsiteRegStart = now - one_day
        self.event.save()
        response = self.client.get(reverse("registration:onsite"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], self.event)
        self.assertIn(b"Onsite Registration", response.content)

    def test_onsite_closed_upcoming(self):
        self.event.onsiteRegStart = now + one_day
        self.event.save()
        response = self.client.get(reverse("registration:onsite"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], self.event)
        self.assertIn(b"not yet open", response.content)

    def test_onsite_closed_ended(self):
        self.event.onsiteRegEnd = now - one_day
        self.event.save()
        response = self.client.get(reverse("registration:onsite"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], self.event)
        self.assertIn(b"has ended", response.content)

    def test_onsite_checkout_cost(self):
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(self.price_45, options)

        response = self.client.get(reverse("registration:onsite_cart"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event, response.context["event"])
        self.assertEqual(
            self.price_45.basePrice + self.option_shirt.optionPrice,
            response.context["total"],
        )
        self.assertEqual(len(response.context["orderItems"]), 1)

        self.checkout()

    def test_onsite_checkout_free(self):
        pass

    def test_onsite_checkout_minor(self):
        pass

    def test_onsite_checkout_discount(self):
        pass

    def test_onsite_done(self):
        response = self.client.get(reverse("registration:onsite_done"))
        self.assertEqual(response.status_code, 200)


@override_settings(
    **{
        "MQTT_BROKER": {
            "host": "localhost",
            "port": 1883,
        },
        "MQTT_JWT_SECRET": "secret==",
        "MQTT_JWT_ALGORITHM": "HS256",
        "REGISTER_KEY": "",
        "REGISTER_PRINTER_URI": "",
    }
)
class TestOnsiteAdmin(OnsiteBaseTestCase):
    def test_onsite_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("registration:onsite_admin"), follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next={0}".format(reverse("registration:onsite_admin")),
        )

    def test_onsite_admin_required(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="john", password="john"))
        response = self.client.get(reverse("registration:onsite_admin"), follow=True)
        self.assertContains(response, "403 Forbidden", status_code=403)
        self.client.logout()

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_admin(self, mock_send_mqtt_message):
        self.client.logout()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(reverse("registration:onsite_admin"), follow=True)
        self.assertEqual(response.status_code, 200)

        self.terminal.delete()
        response = self.client.get(reverse("registration:onsite_admin"))
        self.assertEqual(response.status_code, 200)

        self.terminal = Firebase(token="test", name="Terminal 1")
        self.terminal.save()

        response = self.client.get(
            reverse("registration:onsite_admin"),
            {"search": "Christian", "terminal": "1000"},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("registration:onsite_admin"),
            {"search": "Christian", "terminal": "notastring"},
        )
        self.assertEqual(response.status_code, 200)

        self.client.logout()

    def test_onsite_admin_search_no_query(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:onsite_admin_search"),
        )
        self.assertEqual(response.status_code, 302)

    def test_onsite_admin_search_no_result(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:onsite_admin_search"),
            {"search": "Somethingthatcantpossiblyexistyet"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 0)

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_admin_cart_no_donations(self, mock_send_mqtt_message):
        # Stage registration
        self.assertTrue(self.client.login(username="admin", password="admin"))
        badge_id = self.stage_order()

        # Do search
        response = self.client.get(
            reverse("registration:onsite_admin_search"),
            {"search": "Christian"},
        )
        self.assertEqual(response.status_code, 200)
        attendee = Badge.objects.get(pk=response.json()["results"][0]["id"]).attendee
        attendee.holdType = self.boogeyman_hold
        attendee.save()

        badge_id = response.json()["results"][0]["id"]

        response = self.client.get(
            reverse("registration:onsite_cart_expand"), {"id": [badge_id]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["badge_ids"], [badge_id])

        response = self.client.get(
            reverse("registration:onsite_admin_cart"),
            {"id": badge_id},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()

        self.assertEqual(message["result"][0]["holdType"], self.boogeyman_hold.name)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertEqual(message["badge_ids"], [badge_id])
        self.assertEqual(
            float(message["total"]),
            float(self.price_45.basePrice + self.option_shirt.optionPrice),
        )

        topics = [call.args[0] for call in mock_send_mqtt_message.call_args_list]
        self.assertTrue(any("payment/cart/update" in topic for topic in topics))

        return badge_id

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_terminal_id_not_an_int(self, mock_send_mqtt_message):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(
            reverse("registration:onsite_regtoken"),
            headers={"X-Terminal-Id": "notanint"},
        )

        message = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(message["success"])
        self.assertEqual(message["reason"], "No terminal associated with request")
        mock_send_mqtt_message.assert_not_called()

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_terminal_dne(self, mock_send_mqtt_message):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(
            reverse("registration:onsite_regtoken"),
            headers={"X-Terminal-Id": "1000"},
        )

        message = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(message["success"])
        self.assertEqual(
            message["reason"],
            "No terminal associated with request",
        )
        mock_send_mqtt_message.assert_not_called()

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_terminal_bad_request(self, mock_send_mqtt_message):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(
            reverse("registration:onsite_regtoken"),
        )

        message = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(message["success"])
        self.assertEqual(message["reason"], "No terminal associated with request")
        mock_send_mqtt_message.assert_not_called()

    @patch("registration.payments.create_square_order", return_value="order-123")
    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_enabled_terminal(self, mock_send_mqtt_message, mock_create_order):
        badge_id = self.test_onsite_admin_cart_no_donations()
        self.terminal.payment_type = Firebase.MQTT_REGISTER_APP
        self.terminal.save()

        response = self.client.post(
            reverse("registration:enable_payment"),
            json.dumps({"badge_ids": [badge_id]}),
            content_type="application/json",
            headers={
                "idempotency-key": "abc-123",
                "X-Terminal-Id": str(self.terminal.id),
            },
        )
        self.assertEqual(response.status_code, 200)

        process_calls = [
            call
            for call in mock_send_mqtt_message.call_args_list
            if "payment/process" in call.args[0]
        ]
        self.assertEqual(len(process_calls), 1)
        self.assertEqual(process_calls[0].args[1]["paymentAttemptId"], "abc-123")

    @patch("registration.mqtt.send_mqtt_message")
    def test_complete_cash_transaction(self, mock_send_mqtt_message):
        badge_id = self.test_onsite_admin_cart_no_donations()
        order = Order.objects.last()

        response = self.client.post(
            reverse("registration:complete_cash_transaction"),
            json.dumps({"badge_ids": [badge_id], "tendered": "100.00"}),
            content_type="application/json",
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        self.assertEqual(response.status_code, 200)
        message = response.json()
        self.assertTrue(message["success"])

        total = Decimal(str(message["total"]))
        self.assertEqual(total, self.price_45.basePrice + self.option_shirt.optionPrice)
        self.assertEqual(Decimal(str(message["change"])), Decimal("100.00") - total)

        order.refresh_from_db()
        self.assertEqual(order.billingType, Order.CASH)
        self.assertEqual(order.status, Order.COMPLETED)
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.total, total)
        self.assertEqual(drawer.position_id, self.terminal.id)

    @patch("registration.mqtt.send_mqtt_message")
    def test_complete_cash_transaction_multi_order(self, mock_send_mqtt_message):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        badge_a = self.stage_order(email="a@host", badge_name="A")
        badge_b = self.stage_order(email="b@host", badge_name="B")

        order_a = Badge.objects.get(pk=badge_a).getOrder()
        order_b = Badge.objects.get(pk=badge_b).getOrder()
        self.assertNotEqual(order_a.reference, order_b.reference)

        response = self.client.post(
            reverse("registration:complete_cash_transaction"),
            json.dumps({"badge_ids": [badge_a, badge_b], "tendered": "1000.00"}),
            content_type="application/json",
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        surviving = Order.objects.filter(status=Order.COMPLETED)
        self.assertTrue(surviving.exists())
        for badge_id in (badge_a, badge_b):
            self.assertEqual(
                Badge.objects.get(pk=badge_id).getOrder().status, Order.COMPLETED
            )

    @patch("registration.mqtt.send_mqtt_message")
    @patch("registration.payments.refresh_payment")
    def test_complete_square_transaction(
        self, mock_refresh_payment, mock_send_mqtt_message
    ):
        mock_refresh_payment.return_value = (True, None)
        self.test_onsite_admin_cart_no_donations()
        order = Order.objects.last()
        args = {
            "reference": order.reference,
            "paymentId": "JUNK",
        }
        response = self.client.post(
            reverse("registration:complete_square_transaction"),
            json.dumps(args),
            content_type="application/json",
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )
        self.assertEqual(response.status_code, 200)
        message = response.json()
        self.assertTrue(message["success"])
        order.refresh_from_db()
        self.assertEqual(order.billingType, Order.CREDIT)
        self.assertEqual(order.status, Order.COMPLETED)
        mock_refresh_payment.assert_called_once()


@override_settings(
    MQTT_JWT_SECRET="secret==",
    MQTT_JWT_ALGORITHM="HS256",
    REGISTER_PRINTER_URI="",
)
class TestDrawers(OnsiteBaseTestCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_drawerStatusClosed_no_transactions(self):
        response = self.client.get(reverse("registration:drawer_status"))
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(message["success"])

    def test_drawerStatusClosed(self):
        Cashdrawer(total=100, action=Cashdrawer.OPEN).save()
        Cashdrawer(total=-100, action=Cashdrawer.CLOSE).save()
        response = self.client.get(reverse("registration:drawer_status"))
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertEqual(message["status"], "CLOSED")
        self.assertEqual(Decimal(message["total"]), Decimal("0.00"))

    def test_drawerStatusOpen(self):
        Cashdrawer(total=100, action=Cashdrawer.OPEN).save()
        response = self.client.get(reverse("registration:drawer_status"))
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertEqual(message["status"], "OPEN")
        self.assertEqual(Decimal(message["total"]), Decimal("100.00"))

    def test_drawerStatusShort(self):
        Cashdrawer(total=100, action=Cashdrawer.OPEN).save()
        Cashdrawer(total=-120, action=Cashdrawer.CLOSE).save()
        response = self.client.get(reverse("registration:drawer_status"))
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertEqual(message["status"], "SHORT")
        self.assertEqual(Decimal(message["total"]), Decimal("-20.00"))

    @patch("registration.mqtt.send_mqtt_message")
    def test_open_drawer(self, mock_send_mqtt_message):
        response = self.client.post(
            reverse("registration:open_drawer"),
            {"amount": "200"},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.action, Cashdrawer.OPEN)
        self.assertEqual(drawer.total, 200)
        mock_send_mqtt_message.assert_called_once()

    @patch("registration.mqtt.send_mqtt_message")
    def test_cash_deposit(self, mock_send_mqtt_message):
        response = self.client.post(
            reverse("registration:cash_deposit"),
            {"amount": "200"},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.action, Cashdrawer.DEPOSIT)
        self.assertEqual(drawer.total, 200)
        mock_send_mqtt_message.assert_called_once()

    @patch("registration.mqtt.send_mqtt_message")
    def test_safe_drop(self, mock_send_mqtt_message):
        response = self.client.post(
            reverse("registration:safe_drop"),
            {"amount": "200"},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.action, Cashdrawer.DROP)
        self.assertEqual(drawer.total, -200)
        mock_send_mqtt_message.assert_called_once()

    @patch("registration.mqtt.send_mqtt_message")
    def test_cash_pickup(self, mock_send_mqtt_message):
        response = self.client.post(
            reverse("registration:cash_pickup"),
            {"amount": "200"},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.action, Cashdrawer.PICKUP)
        self.assertEqual(drawer.total, -200)
        mock_send_mqtt_message.assert_called_once()

    @patch("registration.mqtt.send_mqtt_message")
    def test_close_drawer(self, mock_send_mqtt_message):
        response = self.client.post(
            reverse("registration:close_drawer"),
            {"amount": "200"},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.action, Cashdrawer.CLOSE)
        self.assertEqual(drawer.total, -200)
        mock_send_mqtt_message.assert_called_once()

    @patch("registration.mqtt.send_mqtt_message")
    def test_no_sale(self, mock_send_mqtt_message):
        response = self.client.post(
            reverse("registration:no_sale"),
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        mock_send_mqtt_message.assert_called_once()


class TestSearchFields(OnsiteBaseTestCase):
    def test_search_fields_parse(self):
        fields = onsite_admin.SearchFields.parse("")
        self.assertEqual(fields.query, "")
        self.assertIsNone(fields.birthday)
        self.assertIsNone(fields.badge_ids)

        fields = onsite_admin.SearchFields.parse(" test query ")
        self.assertEqual(fields.query, "test query")
        self.assertIsNone(fields.birthday)
        self.assertIsNone(fields.badge_ids)

        fields = onsite_admin.SearchFields.parse(" test query birthday:1990-01-01 ")
        self.assertEqual(fields.query, "test query")
        self.assertEqual(fields.birthday, "1990-01-01")
        self.assertIsNone(fields.badge_ids)

        fields = onsite_admin.SearchFields.parse("num:123,456")
        self.assertEqual(fields.query, "")
        self.assertIsNone(fields.birthday)
        self.assertEqual(fields.badge_ids, [123, 456])


class TestDualAuth(OnsiteBaseTestCase):
    def _search_url(self):
        return reverse("registration:onsite_admin_search") + "?search=nobody"

    def test_bearer_token_ok(self):
        response = self.client.get(
            self._search_url(),
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_bad_token_401(self):
        response = self.client.get(
            self._search_url(),
            headers={"authorization": "Bearer not-a-real-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_anonymous_401(self):
        response = self.client.get(self._search_url())
        self.assertEqual(response.status_code, 401)

    def test_session_without_perm_403(self):
        User.objects.create_user("staff", "staff@host", "staff", is_staff=True)
        self.assertTrue(self.client.login(username="staff", password="staff"))
        response = self.client.post(
            reverse("registration:complete_cash_transaction"),
            json.dumps({"badge_ids": [1], "tendered": "10"}),
            content_type="application/json",
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        self.assertEqual(response.status_code, 403)

    @patch("registration.mqtt.send_mqtt_message")
    def test_token_bypasses_permission(self, mock_send):
        badge_id = self.stage_order()
        response = self.client.post(
            reverse("registration:complete_cash_transaction"),
            json.dumps({"badge_ids": [badge_id], "tendered": "100.00"}),
            content_type="application/json",
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    @patch("registration.mqtt.send_mqtt_message")
    def test_csrf_enforced_on_session_post(self, mock_send):
        csrf_client = Client(enforce_csrf_checks=True)
        self.assertTrue(csrf_client.login(username="admin", password="admin"))
        response = csrf_client.post(
            reverse("registration:onsite_regtoken"),
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        self.assertEqual(response.status_code, 403)

    @patch("registration.mqtt.send_mqtt_message")
    def test_csrf_exempt_on_bearer_post(self, mock_send):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("registration:onsite_regtoken"),
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )
        self.assertEqual(response.status_code, 200)

    def _restricted_terminal(self):
        return Firebase.objects.create(
            token="restricted", name="Payment Only", web_access=False
        )

    def test_restricted_terminal_web_read_forbidden(self):
        restricted = self._restricted_terminal()
        response = self.client.get(
            self._search_url(),
            headers={"authorization": f"Bearer {restricted.token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_restricted_terminal_web_write_forbidden(self):
        restricted = self._restricted_terminal()
        response = self.client.post(
            reverse("registration:assign_badge_number"),
            json.dumps([]),
            content_type="application/json",
            headers={"authorization": f"Bearer {restricted.token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_restricted_terminal_square_complete_allowed(self):
        restricted = self._restricted_terminal()
        response = self.client.post(
            reverse("registration:complete_square_transaction"),
            json.dumps({}),
            content_type="application/json",
            headers={"authorization": f"Bearer {restricted.token}"},
        )
        self.assertEqual(response.status_code, 400)

    @patch("registration.views.onsite_admin.cache.set")
    @patch("registration.views.onsite_admin.send_mqtt_message_to_terminal")
    def test_restricted_terminal_square_authorization_allowed(
        self, mock_send, mock_cache_set
    ):
        restricted = self._restricted_terminal()
        response = self.client.get(
            reverse("registration:terminal_square_token"),
            headers={"authorization": f"Bearer {restricted.token}"},
        )

        self.assertEqual(response.status_code, 200)
        mock_cache_set.assert_called_once()
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], restricted)
        self.assertEqual(mock_send.call_args.args[1], "web/authorize/square")

    def test_restricted_terminal_staff_session_ok(self):
        restricted = self._restricted_terminal()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            self._search_url(),
            headers={"X-Terminal-Id": str(restricted.id)},
        )
        self.assertEqual(response.status_code, 200)


class TestCartExpand(OnsiteBaseTestCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_expand_returns_self_for_single_order(self):
        badge_id = self.stage_order()
        response = self.client.get(
            reverse("registration:onsite_cart_expand"), {"id": [badge_id]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["badge_ids"], [badge_id])

    def test_expand_rejects_bad_badge_id(self):
        response = self.client.get(
            reverse("registration:onsite_cart_expand"), {"id": ["notanint"]}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["reason"], "Unexpected badge ID value")

    def test_cart_rejects_bad_badge_id(self):
        response = self.client.get(
            reverse("registration:onsite_admin_cart"), {"id": ["notanint"]}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["reason"], "Unexpected badge ID value")

    def test_expand_unknown_badge_returns_empty(self):
        response = self.client.get(
            reverse("registration:onsite_cart_expand"), {"id": [999999]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["badge_ids"], [])


class TestDiscount(OnsiteBaseTestCase):
    @patch("registration.mqtt.send_mqtt_message")
    def test_discount_attribution_terminal(self, mock_send):
        badge_id = self.stage_order()
        response = self.client.post(
            reverse("registration:onsite_create_discount"),
            json.dumps({"type": "Amount", "value": "10", "badge_ids": [badge_id]}),
            content_type="application/json",
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        discount = Discount.objects.last()
        self.assertIn(f"terminal [{self.terminal.name}]", discount.notes)
        self.assertEqual(discount.amountOff, Decimal("10"))

        order = Badge.objects.get(pk=badge_id).getOrder()
        self.assertEqual(order.discount_id, discount.id)

    @patch("registration.mqtt.send_mqtt_message")
    def test_discount_attribution_user(self, mock_send):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        badge_id = self.stage_order()
        response = self.client.post(
            reverse("registration:onsite_create_discount"),
            json.dumps({"type": "Percent", "value": "50", "badge_ids": [badge_id]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        discount = Discount.objects.last()
        self.assertIn("Applied by [admin]", discount.notes)
        self.assertEqual(discount.percentOff, Decimal("50"))

    @patch("registration.mqtt.send_mqtt_message")
    def test_comp_discount_completes_order(self, mock_send):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        badge_id = self.stage_order()
        order = Badge.objects.get(pk=badge_id).getOrder()
        self.assertEqual(order.billingType, Order.UNPAID)

        response = self.client.post(
            reverse("registration:onsite_create_discount"),
            json.dumps({"type": "Percent", "value": "100", "badge_ids": [badge_id]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(order.billingType, Order.COMP)
        self.assertEqual(order.status, Order.COMPLETED)
        self.assertEqual(order.total, Decimal("0"))
        self.assertEqual(Badge.objects.get(pk=badge_id).abandoned, Badge.COMP)
        self.assertEqual(order.discount.used, 1)


class TestBuildResultPruning(OnsiteBaseTestCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_two_consecutive_missing_ids_pruned(self):
        badge_id = self.stage_order()
        data = onsite_admin.build_result([999998, 999999, badge_id])
        self.assertEqual(data["badge_ids"], [badge_id])


class TestAssignBadgeTokenAuth(OnsiteBaseTestCase):
    @patch("registration.mqtt.send_mqtt_message")
    def test_assign_badge_number_token_auth(self, mock_send):
        badge_id = self.stage_order()
        response = self.client.post(
            reverse("registration:assign_badge_number"),
            json.dumps([{"id": badge_id}]),
            content_type="application/json",
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )
        self.assertIn(response.status_code, (200, 400))
        self.assertIn("success", response.json())


class TestOrderlessBadge(OnsiteBaseTestCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(self.client.login(username="admin", password="admin"))

        attendee = Attendee.objects.create(
            firstName="No",
            lastName="Order",
            address1="1 Street",
            city="City",
            state="ST",
            country="US",
            postalCode="12345",
            phone="5551234567",
            email="no@order.test",
            birthdate="1990-01-01",
        )
        self.orderless_badge = Badge.objects.create(
            attendee=attendee, event=self.event, badgeName="Orderless"
        )

    def test_get_order_returns_none(self):
        self.assertIsNone(self.orderless_badge.getOrder())

    def test_cart_prunes_orderless_badge(self):
        badge_id = self.stage_order()

        response = self.client.get(
            reverse("registration:onsite_admin_cart"),
            {"id": [self.orderless_badge.id, badge_id]},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["badge_ids"], [badge_id])

    def test_cart_with_only_orderless_badge(self):
        response = self.client.get(
            reverse("registration:onsite_admin_cart"),
            {"id": [self.orderless_badge.id]},
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["badge_ids"], [])


class TestCartClearsTerminal(OnsiteBaseTestCase):
    @patch("registration.mqtt.send_mqtt_message")
    def test_empty_cart_publishes_clear(self, mock_send):
        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(
            reverse("registration:onsite_admin_cart"),
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )

        self.assertEqual(response.status_code, 200)
        topics = [call.args[0] for call in mock_send.call_args_list]
        self.assertTrue(any("payment/cart/clear" in topic for topic in topics))


class TestRequireTerminal(OnsiteBaseTestCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_missing_terminal_header_rejected(self):
        response = self.client.post(reverse("registration:onsite_regtoken"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["reason"], "No terminal associated with request"
        )

    @patch("registration.mqtt.send_mqtt_message")
    def test_terminal_header_accepted(self, mock_send):
        response = self.client.post(
            reverse("registration:onsite_regtoken"),
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_cash_drawer_still_rejects_terminal_token(self):
        self.client.logout()
        response = self.client.post(
            reverse("registration:no_sale"),
            headers={"authorization": f"Bearer {self.terminal.token}"},
        )

        self.assertNotEqual(response.status_code, 200)


class TestCashTransactionScope(OnsiteBaseTestCase):
    @patch("registration.mqtt.send_mqtt_message")
    def test_unrelated_order_sharing_reference_survives(self, mock_send):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        badge_id = self.stage_order(email="cart@host", badge_name="InCart")
        other_badge_id = self.stage_order(email="other@host", badge_name="NotInCart")

        in_cart = Badge.objects.get(pk=badge_id).getOrder()
        bystander = Badge.objects.get(pk=other_badge_id).getOrder()

        bystander.reference = in_cart.reference
        bystander.save()
        status_before = bystander.status

        response = self.client.post(
            reverse("registration:complete_cash_transaction"),
            json.dumps({"badge_ids": [badge_id], "tendered": "1000.00"}),
            content_type="application/json",
            headers={"X-Terminal-Id": str(self.terminal.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        bystander.refresh_from_db()
        self.assertEqual(bystander.status, status_before)
        self.assertEqual(
            Badge.objects.get(pk=other_badge_id).getOrder().id, bystander.id
        )


class TestSessionPing(OnsiteBaseTestCase):
    def test_ping_requires_staff_session(self):
        response = self.client.get(reverse("registration:onsite_admin_ping"))
        self.assertNotEqual(response.status_code, 200)

    def test_ping_marks_session_modified(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(reverse("registration:onsite_admin_ping"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SQUARE_APPLICATION_SECRET="test-secret",
)
class TestSquareOAuth(OnsiteBaseTestCase):
    def setUp(self):
        super().setUp()

        self.state = "test-oauth-state"
        self.cache_key = onsite_admin._square_oauth_cache_key(self.state)

        onsite_admin.cache.clear()
        onsite_admin.cache.set(self.cache_key, self.terminal.id, timeout=600)

    def _url(self, **params):
        return reverse("registration:oauth_square") + "?" + urlencode(params)

    def _stored_terminal(self):
        return onsite_admin.cache.get(self.cache_key)

    @patch("registration.payments.client")
    def test_unknown_state_rejected(self, mock_client):
        response = self.client.get(self._url(state="not-the-state", code="abc"))

        self.assertEqual(response.status_code, 400)
        mock_client.o_auth.obtain_token.assert_not_called()

    @patch("registration.payments.client")
    def test_denied_authorization_keeps_state(self, mock_client):
        response = self.client.get(self._url(state=self.state, error="access_denied"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["reason"], "access_denied")
        mock_client.o_auth.obtain_token.assert_not_called()

        self.assertEqual(self._stored_terminal(), self.terminal.id)

    @patch("registration.payments.client")
    def test_failed_exchange_keeps_state(self, mock_client):
        mock_client.o_auth.obtain_token.side_effect = Exception("boom")

        with self.assertLogs("registration.views.onsite_admin", level="ERROR"):
            response = self.client.get(self._url(state=self.state, code="abc"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._stored_terminal(), self.terminal.id)
        mock_client.o_auth.obtain_token.assert_called_once()

    @patch("registration.views.onsite_admin.send_mqtt_message_to_terminal")
    @patch("registration.payments.client")
    def test_successful_exchange_consumes_state(self, mock_client, mock_send):
        mock_client.o_auth.obtain_token.return_value = SimpleNamespace(
            access_token="access", refresh_token="refresh"
        )

        response = self.client.get(self._url(state=self.state, code="abc"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            mock_client.o_auth.obtain_token.call_args.kwargs["code"], "abc"
        )

        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], self.terminal)
        self.assertEqual(mock_send.call_args.args[1], "payment/update/token")
        self.assertEqual(
            mock_send.call_args.args[2],
            {"accessToken": "access", "refreshToken": "refresh"},
        )

        self.assertIsNone(self._stored_terminal())
