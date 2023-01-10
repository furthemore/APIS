import json

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse
from mock import patch

from registration.admin import FirebaseAdmin
from registration.models import Firebase
from registration.pushy import PushyError


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

        provision_dict = json.loads(provision_json)

        current_site = Site.objects.get_current()
        endpoint = "https://{0}{1}".format(current_site.domain, reverse("root"))

        expected_result = {
            "v": 1,
            "client_id": settings.SQUARE_APPLICATION_ID,
            "api_key": settings.REGISTER_KEY,
            "endpoint": endpoint,
            "name": firebase.name,
            "location_id": settings.REGISTER_SQUARE_LOCATION,
            "force_location": settings.REGISTER_FORCE_LOCATION,
            "bg": firebase.background_color,
            "fg": firebase.foreground_color,
            "webview": firebase.webview,
        }

        self.assertEqual(provision_dict, expected_result)

    @patch("registration.pushy.PushyAPI.send_push_notification")
    def test_save_model(self, mock_send_push_notification):
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
        mock_send_push_notification.assert_called_once()

    @patch("registration.pushy.PushyAPI.send_push_notification")
    def test_save_model_pushy_exception(self, mock_send_push_notification):
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

        mock_send_push_notification.side_effect = PushyError()

        response = self.client.post(
            reverse("admin:registration_firebase_change", args=(terminal_red.id,)),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"there was a problem", response.content)
        mock_send_push_notification.assert_called_once()

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
        self.assertIn(b'height="77mm"', response.content)

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
