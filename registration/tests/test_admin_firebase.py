from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse

from registration.admin import FirebaseAdmin
from registration.models import Firebase
from registration import mqtt


class TestFirebaseAdmin(TestCase):
    def setUp(self):
        # Create some users
        self.admin_user = User.objects.create_superuser("admin", "admin@host", "admin")
        self.admin_user.save()
        self.normal_user = User.objects.create_user(
            "john", "john@thebeatles.com", "john"
        )
        self.normal_user.staff_member = False
        self.normal_user.save()

        self.terminal_blue = Firebase(token="terminal_blue_token", name="Blue")
        self.terminal_blue.save()

    def test_get_provisioning(self):
        firebase = self.terminal_blue
        provision_json = FirebaseAdmin.get_provisioning(firebase)

        provision_dict = provision_json

        current_site = Site.objects.get_current()
        endpoint = "https://{0}".format(current_site.domain)
        token = mqtt.get_client_token(firebase)

        expected_result = {
            "terminalName": firebase.name,
            "endpoint": endpoint,
            "token": firebase.token,
            "webViewUrl": firebase.webview,
            "themeColor": firebase.background_color,
            "mqttHost": settings.MQTT_EXTERNAL_BROKER,
            "mqttPort": 443,
            "mqttUsername": token["user"],
            "mqttPassword": token["token"],
            "mqttTopic": f'{mqtt.get_topic("terminal", firebase.name)}/action',
            "squareApplicationId": settings.SQUARE_APPLICATION_ID,
            "squareLocationId": settings.REGISTER_SQUARE_LOCATION,
        }

        self.assertEqual(provision_dict, expected_result)

    @patch("registration.mqtt.send_mqtt_message")
    def test_save_model(self, mock_send_mqtt_message):
        self.client.logout()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        terminal_red = Firebase(token="terminal_red_token", name="Not Red Yet")
        terminal_red.save()

        form_data = {
            "token": terminal_red.token,
            "name": "Red",
            "background_color": "#ff0000",
            "foreground_color": "#ffffff",
        }

        response = self.client.post(
            reverse("admin:registration_firebase_change", args=(terminal_red.id,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"there was a problem", response.content)
        terminal_red.refresh_from_db()
        self.assertEqual(terminal_red.name, "Red")
        mock_send_mqtt_message.assert_called_once()

    def test_get_qrcode(self):
        qr_code = FirebaseAdmin.get_qrcode("foo")
        self.assertIn(b"<?xml version='1.0' encoding='UTF-8'?>\n<svg ", qr_code)
        self.assertIn(b'height="29mm"', qr_code)

    def test_provision_page_superuser(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("admin:firebase_provision", args=(self.terminal_blue.id,))
        )
        self.assertNotIn(
            b"You must be a superuser to access this URL", response.content
        )
        self.assertIn(
            b"<?xml version='1.0' encoding='UTF-8'?>\n<svg ",
            response.content,
        )
        self.assertIn(b'height="113mm"', response.content)

    def test_provision_page_normal_user(self):
        self.assertTrue(self.client.login(username="john", password="john"))
        response = self.client.get(
            reverse("admin:firebase_provision", args=(self.terminal_blue.id,))
        )

        self.assertIn(b"You must be a superuser to access this URL", response.content)

    def test_change_form_superuser(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(
            reverse("admin:registration_firebase_change", args=(self.terminal_blue.id,))
        )
        self.assertIn(b"Provision App", response.content)

    def test_change_form_normal_user(self):
        self.assertTrue(self.client.login(username="john", password="john"))
        response = self.client.get(
            reverse("admin:registration_firebase_change", args=(self.terminal_blue.id,))
        )
        self.assertNotIn(b"Provision App", response.content)
