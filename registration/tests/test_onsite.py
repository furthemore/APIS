import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from registration.models import *
from registration.tests.common import *
from registration.views import onsite_admin


class OnsiteBaseTestCase(TestCase):
    def setUp(self):
        # Create some users
        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.admin_user.save()
        self.normal_user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "john"
        )
        self.normal_user.staff_member = False
        self.normal_user.save()

        # Create some test terminals to push notifications to
        self.terminal = Firebase(token="test", name="Terminal 1")
        self.terminal.save()

        # At least one event always mandatory
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()

        self.price_45 = PriceLevel(
            name="Attendee",
            description="Some test description here",
            basePrice=45.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )
        self.price_45.save()
        self.price_90 = PriceLevel(
            name="Sponsor",
            description="Woot!",
            basePrice=90.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )
        self.price_90.save()

        self.option_conbook = PriceLevelOption(
            optionName="Conbook", optionPrice=0.00, optionExtraType="bool"
        )
        self.option_conbook.save()
        self.option_shirt = PriceLevelOption(
            optionName="Shirt Size", optionPrice=20.00, optionExtraType="ShirtSizes"
        )
        self.option_shirt.save()
        self.option_100_int = PriceLevelOption(
            optionName="Something Pricy", optionPrice=100.00, optionExtraType="int"
        )
        self.option_100_int.save()

        self.shirt1 = ShirtSizes(name="Test_Large")
        self.shirt1.save()

        self.client = Client()
        self.boogeyman_hold = HoldType(name="Boogeyman")
        self.boogeyman_hold.save()

    def add_to_cart(self, level, options):
        form_data = {
            "attendee": {
                "address1": "Voluptas dolor dicta",
                "address2": "Debitis deleniti und",
                "asl": "",
                "badgeName": "Onsite Badge 1",
                "birthdate": "1989-02-07",
                "city": "64133",
                "country": "SK",
                "email": "apis@mailinator.com",
                "emailsOk": False,
                "firstName": "Cameron",
                "lastName": "Christian",
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
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
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


@override_settings(**{
    "MQTT_BROKER": {
        "host": "localhost",
        "port": 1883,
    },
    "MQTT_JWT_SECRET": "secret==",
    "MQTT_JWT_ALGORITHM": "HS256",
    "REGISTER_KEY": "",
    "REGISTER_PRINTER_URI": "",
})
class TestOnsiteAdmin(OnsiteBaseTestCase):
    def test_onsite_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("registration:onsite_admin"), follow=True)
        self.assertRedirects(
            response,
            "/admin/login/?next={0}".format(reverse("registration:onsite_admin")),
        )

    def test_onsite_admin_required(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="john", password="john"))
        response = self.client.get(reverse("registration:onsite_admin"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "are not authorized to access this page")
        self.client.logout()

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_admin(self, mock_send_mqtt_message):
        self.client.logout()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(reverse("registration:onsite_admin"), follow=True)
        self.assertEqual(response.status_code, 200)
        settings = json.loads(response.context["settings"])
        self.assertEqual(len(settings["errors"]), 0)
        self.assertEqual(len(settings["terminals"]["available"]), 1)

        self.terminal.delete()
        response = self.client.get(reverse("registration:onsite_admin"))
        self.assertEqual(response.status_code, 200)
        errors = [e["code"] for e in json.loads(response.context["settings"])["errors"]]
        self.assertTrue("ERROR_NO_TERMINAL" in errors)

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
    def test_onsite_admin_cart_no_donations(
        self, mock_send_mqtt_message
    ):
        # Stage registration
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(self.price_45, options)
        self.checkout()

        self.assertTrue(self.client.login(username="admin", password="admin"))

        # Do search
        response = self.client.get(
            reverse("registration:onsite_admin_search"),
            {"search": "Christian"},
        )
        self.assertEqual(response.status_code, 200)
        attendee = Badge.objects.get(pk=response.json()["results"][0]["id"]).attendee
        attendee.holdType = self.boogeyman_hold
        attendee.save()

        response = self.client.get(
            reverse("registration:onsite_admin_search"),
            {"search": "Christian", "terminal": self.terminal.id},
        )
        self.assertEqual(response.status_code, 200)

        # Add to cart
        badge_id = response.json()["results"][0]["id"]

        response = self.client.get(
            reverse("registration:onsite_add_to_cart"),
            {"id": badge_id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["cart"], [badge_id])

        response = self.client.get(reverse("registration:onsite_admin_cart"))
        message = response.json()

        self.assertEqual(message["result"][0]["holdType"], self.boogeyman_hold.name)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertEqual(
            float(message["total"]),
            float(self.price_45.basePrice + self.option_shirt.optionPrice),
        )

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_set_terminal_status(
        self, mock_send_mqtt_single
    ):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:terminal_status"),
            {"terminal": self.terminal.id, "status": "open"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_send_mqtt_single.call_count, 2)

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_set_invalid_terminal_status(self, mock_send_mqtt_message):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:terminal_status"),
            {"terminal": "notanint", "status": "open"},
        )

        message = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(message["success"])
        self.assertEqual(message["reason"], "No terminal associated with request")
        mock_send_mqtt_message.assert_not_called()

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_terminal_dne(
        self, mock_send_mqtt_message
    ):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:terminal_status"),
            {"terminal": 1000},
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
    def test_onsite_terminal_bad_request(
        self, mock_send_mqtt_message
    ):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:terminal_status"),
        )

        message = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(message["success"])
        self.assertEqual(
            message["reason"], "No terminal associated with request"
        )
        mock_send_mqtt_message.assert_not_called()

    @patch("registration.mqtt.send_mqtt_message")
    def test_onsite_enabled_terminal(self, mock_send_mqtt_message):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("registration:enable_payment"),
            {"terminal": self.terminal.id},
        )
        self.assertEqual(response.status_code, 200)

    def test_firebase_register_bad_key(self):
        response = self.client.get(
            reverse("registration:firebase_register"),
            {
                "key": "garbedygook",
                "token": str(uuid.uuid4()),
                "name": "Some New Terminal 2",
            },
        )
        message = response.json()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(message["success"])
        self.assertEqual(message["reason"], "Incorrect API key")

    def test_firebase_register_bad_request(self):
        response = self.client.get(
            reverse("registration:firebase_register"),
            {"key": settings.REGISTER_KEY},
        )
        message = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(message["success"])
        self.assertEqual(message["reason"], "Must specify token and name parameter")

    def test_firebase_register_new_token(self):
        response = self.client.get(
            reverse("registration:firebase_register"),
            {
                "key": settings.REGISTER_KEY,
                "token": str(uuid.uuid4()),
                "name": "Some New Terminal 2",
            },
        )
        message = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertFalse(message["updated"])

    def test_firebase_register_update_token(self):
        new_token = str(uuid.uuid4())
        response = self.client.get(
            reverse("registration:firebase_register"),
            {
                "key": settings.REGISTER_KEY,
                "token": new_token,
                "name": self.terminal.name,
            },
        )
        message = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(message["success"])
        self.assertTrue(message["updated"])
        self.terminal = Firebase.objects.get(name=self.terminal.name)
        self.assertEqual(self.terminal.token, new_token)

    @patch("registration.mqtt.send_mqtt_message")
    def test_complete_cash_transaction(
        self, mock_send_mqtt_message
    ):
        self.test_onsite_admin_cart_no_donations()
        self.client.get(
            reverse("registration:onsite_admin"), {"terminal": self.terminal.name}
        )
        order = Order.objects.last()
        args = {
            "reference": order.reference,
            "total": order.total,
            "tendered": order.total,
        }
        response = self.client.get(
            reverse("registration:complete_cash_transaction"), args
        )
        self.assertEqual(response.status_code, 200)
        message = response.json()
        self.assertTrue(message["success"])
        order.refresh_from_db()
        self.assertEqual(order.billingType, Order.CASH)
        self.assertEqual(order.status, Order.COMPLETED)
        drawer = Cashdrawer.objects.last()
        self.assertEqual(drawer.total, order.total)

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
            reverse("registration:complete_square_transaction"), json.dumps(args), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.terminal.token}"
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
        self.client.get(reverse("registration:onsite_admin"))

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
            reverse("registration:open_drawer"), {"amount": "200"}
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
            reverse("registration:cash_deposit"), {"amount": "200"}
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
            reverse("registration:safe_drop"), {"amount": "200"}
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
            reverse("registration:cash_pickup"), {"amount": "200"}
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
            reverse("registration:close_drawer"), {"amount": "200"}
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
        response = self.client.post(reverse("registration:no_sale"))
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
