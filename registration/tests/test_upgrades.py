import json

from django.test import tag
from django.urls import reverse

from registration.models import *
from registration.tests.common import OrdersTestCase


class TestUpgrades(OrdersTestCase):
    def test_upgrade_index(self):
        guid = "ARSTBCESKFGHAIESTRK"
        response = self.client.get(reverse("registration:upgrade", args=[guid]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, guid)

    def test_infoUpgrade_bad_json(self):
        response = self.client.post(
            reverse("registration:info_upgrade"),
            "notJSON-",
            content_type="application/json",
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"success": False})

    def test_infoUpgrade_wrong_token(self):
        # Failed lookup against info_upgrade()
        attendee = Attendee(**self.attendee_upgrade)
        attendee.save()
        badge = Badge(attendee=attendee, event=self.event, badgeName="Test Upgrade")
        badge.save()
        post_data = {
            "email": attendee.email,
            "token": "notTheRightToken",
            "event": self.event.name,
        }
        response = self.client.post(
            reverse("registration:info_upgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        badge.delete()
        attendee.delete()

    def test_infoUpgrade_wrong_email(self):
        # Failed lookup against info_upgrade()
        attendee = Attendee(**self.attendee_upgrade)
        attendee.save()
        badge = Badge(attendee=attendee, event=self.event, badgeName="Test Upgrade")
        badge.save()
        post_data = {
            "email": "nottherightemail@somewhere.com",
            "token": badge.registrationToken,
        }
        response = self.client.post(
            reverse("registration:info_upgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        badge.delete()
        attendee.delete()

    def test_infoUpgrade_happy_path(self):
        attendee = Attendee(**self.attendee_upgrade)
        attendee.save()
        badge = Badge(attendee=attendee, event=self.event, badgeName="Test Upgrade")
        badge.save()
        post_data = {
            "event": self.event.name,
            "email": badge.attendee.email,
            "token": badge.registrationToken,
        }
        response = self.client.post(
            reverse("registration:info_upgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        badge.delete()
        attendee.delete()

    @tag("square")
    def test_findUpgrade_happy_path(self):
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(self.attendee_form_upgrade, self.price_45, options)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        response = self.checkout("cnon:card-nonce-ok", "0", "0")
        self.assertEqual(response.status_code, 200)

        # Check that user was successfully saved
        attendee = Attendee.objects.get(firstName="Upgrade", lastName="Me")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertEqual(badge.effectiveLevel(), self.price_45)

        post_data = {
            "event": self.event.name,
            "email": badge.attendee.email,
            "token": badge.registrationToken,
        }
        response = self.client.post(
            reverse("registration:info_upgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("registration:find_upgrade"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["attendee"], attendee)
        self.assertEqual(response.context["badge"], badge)

        badge.delete()
        attendee.delete()

    @tag("square")
    def setup_upgrade(self):
        # set up existing registration
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(self.attendee_form_upgrade, self.price_45, options)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        response = self.checkout("cnon:card-nonce-ok", "0", "0")
        self.assertEqual(response.status_code, 200)

        # Check that user was successfully saved
        attendee = Attendee.objects.get(firstName="Upgrade", lastName="Me")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertEqual(badge.effectiveLevel(), self.price_45)

        # info_upgrade()
        post_data = {
            "event": self.event.name,
            "email": badge.attendee.email,
            "token": badge.registrationToken,
        }
        response = self.client.post(
            reverse("registration:info_upgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return badge, attendee

    def upgrade_add_and_checkout(self, price_level, form, badge, attendee):
        # add_upgrade()
        post_data = {
            "event": self.event.name,
            "badge": {
                "id": badge.id,
            },
            "attendee": {
                "id": attendee.id,
            },
            "priceLevel": {
                "id": price_level.id,
                "options": [],
            },
        }
        self.client.post(
            reverse("registration:add_upgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        cart_response = self.client.get(reverse("registration:invoice_upgrade"))

        checkout_response = self.client.post(
            reverse("registration:checkout_upgrade"),
            json.dumps(form),
            content_type="application/json",
        )
        return cart_response, checkout_response

    @tag("square")
    def test_upgrade(self):
        badge, attendee = self.setup_upgrade()
        cart, checkout = self.upgrade_add_and_checkout(
            self.price_90, self.attendee_form_upgrade_checkout, badge, attendee
        )
        self.assertEqual(cart.status_code, 200)
        self.assertEqual(cart.context["total"], self.price_45.basePrice)
        self.assertEqual(cart.context["total_discount"], 0)
        self.assertEqual(cart.status_code, 200)
        self.assertEqual(badge.effectiveLevel(), self.price_90)
        badge.delete()
        attendee.delete()

    @tag("square")
    def test_upgrade_zero(self):
        badge, attendee = self.setup_upgrade()
        cart, checkout = self.upgrade_add_and_checkout(
            self.price_45, self.attendee_form_upgrade_checkout, badge, attendee
        )
        self.assertEqual(checkout.status_code, 200)
        self.assertEqual(badge.effectiveLevel(), self.price_45)
        badge.delete()
        attendee.delete()

    @tag("square")
    def test_upgrade_card_declined(self):
        form = self.attendee_form_upgrade_checkout
        form["nonce"] = "cnon:card-nonce-declined"
        badge, attendee = self.setup_upgrade()
        cart, checkout = self.upgrade_add_and_checkout(
            self.price_45, form, badge, attendee
        )
        self.assertEqual(checkout.status_code, 200)
        self.assertEqual(badge.effectiveLevel(), self.price_45)
        badge.delete()
        attendee.delete()

    def test_upgrade_sad_path(self):
        pass

    def test_new_staff(self):
        pass

    def test_promote_staff(self):
        pass
