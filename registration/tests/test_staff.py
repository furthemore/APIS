import json
from datetime import datetime, timedelta
from unittest.mock import patch

from django.db import DatabaseError, IntegrityError
from django.test import TestCase
from django.test.utils import tag
from django.urls import reverse
from freezegun import freeze_time

from registration.models import *
from registration.tests.common import OrdersTestCase
from registration.views import staff

tz = timezone.get_current_timezone()
now = timezone.now()
one_hour = timedelta(hours=1)
one_day = timedelta(days=1)
ten_days = timedelta(days=10)


class StaffTestCase(OrdersTestCase):
    def setUp(self):
        super().setUp()
        self.token = StaffInvite.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            ignore_time_window=False,
        )
        self.token_used = StaffInvite.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            used=True,
            ignore_time_window=False,
        )
        self.token_expired = StaffInvite.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now - one_hour,
            ignore_time_window=False,
        )
        self.token_override = StaffInvite.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            ignore_time_window=True,
        )
        self.token_used_override = StaffInvite.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            used=True,
            ignore_time_window=True,
        )
        self.token_expired_override = StaffInvite.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now - one_hour,
            ignore_time_window=True,
        )

        self.attendee = Attendee.objects.create(
            firstName="Staffer",
            lastName="Testerson",
            address1="123 Somewhere St",
            city="Place",
            state="PA",
            country="US",
            postalCode=12345,
            phone="1112223333",
            email="apis@mailinator.org",
            birthdate="1990-01-01",
        )
        self.staff = Staff.objects.create(attendee=self.attendee, event=self.event)

        self.badge = Badge.objects.create(
            attendee=self.attendee, event=self.event, badgeName="DisStaff"
        )
        self.attendee2 = Attendee.objects.create(
            firstName="Staph",
            lastName="Testerson",
            address1="123 Somewhere St",
            city="Place",
            state="PA",
            country="US",
            postalCode=12345,
            phone="1112223333",
            email="apis@mailinator.org",
            birthdate="1990-01-01",
        )
        self.staff2 = Staff.objects.create(attendee=self.attendee2, event=self.event)
        self.badge2 = Badge.objects.create(
            attendee=self.attendee2, event=self.event, badgeName="AnotherStaff"
        )


class TestFindReturningStaff(TestCase):
    def test_find_returning_staff_empty(self):
        response = self.client.post(reverse("registration:find_returning_staff"))
        self.assertEqual(response.status_code, 400)

    def test_find_returning_staff_404(self):
        body = {
            "email": "foo",
            "token": "bar",
        }
        response = self.client.post(
            reverse("registration:find_returning_staff"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


class TestNewStaff(StaffTestCase):
    def test_new_staff_invite_good(self):
        body = {
            "email": self.token.email,
            "token": self.token.token,
        }
        response = self.client.post(
            reverse("registration:new_staff", args=(self.token.token,)),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"not yet open", response.content)

    @freeze_time(timezone.now() - timedelta(days=20))
    def test_new_staff_invite_good_closed_upcoming(self):
        body = {
            "email": self.token.email,
            "token": self.token.token,
        }
        response = self.client.post(
            reverse("registration:new_staff", args=(self.token.token,)),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"not yet open", response.content)
        self.assertIn(
            b'<a href="/registration/">Back to Main Page</a>', response.content
        )

    @freeze_time(timezone.now() + timedelta(days=20))
    def test_new_staff_invite_good_closed_ended(self):
        body = {
            "email": self.token.email,
            "token": self.token.token,
        }
        response = self.client.post(
            reverse("registration:new_staff", args=(self.token.token,)),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"has ended", response.content)
        self.assertIn(
            b'<a href="/registration/">Back to Main Page</a>', response.content
        )

    @freeze_time("2000-01-01")
    def test_new_staff_invite_override(self):
        body = {
            "email": self.token_override.email,
            "token": self.token_override.token,
        }
        response = self.client.post(
            reverse("registration:new_staff", args=(self.token_override.token,)),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"not yet open", response.content)


class TestFindNewStaff(StaffTestCase):
    def test_find_new_staff_empty(self):
        response = self.client.post(reverse("registration:find_new_staff"))
        self.assertEqual(response.status_code, 400)

    def test_find_new_staff_404(self):
        body = {
            "email": "foo",
            "token": "bar",
        }
        response = self.client.post(
            reverse("registration:find_new_staff"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_find_new_staff(self):
        body = {
            "email": self.token.email,
            "token": self.token.token,
        }
        response = self.client.post(
            reverse("registration:find_new_staff"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "message": "STAFF"})

    def test_find_new_staff_token_used(self):
        body = {
            "email": self.token_used.email,
            "token": self.token_used.token,
        }
        response = self.client.post(
            reverse("registration:find_new_staff"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"success": False, "reason": "Token Used"})

    def test_find_new_staff_token_expired(self):
        body = {
            "email": self.token_expired.email,
            "token": self.token_expired.token,
        }
        response = self.client.post(
            reverse("registration:find_new_staff"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"success": False, "reason": "Invalid Token"})


class TestInfoNewStaff(StaffTestCase):
    def test_info_new_staff_404(self):
        result = self.client.get(reverse("registration:info_new_staff"))
        self.assertEqual(result.status_code, 404)

    def test_info_new_staff(self):
        session = self.client.session
        session["new_staff"] = self.token.token
        session.save()
        result = self.client.get(reverse("registration:info_new_staff"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["token"].token, self.token.token)


class TestAddNewStaff(StaffTestCase):
    def test_add_new_staff(self):
        body = {
            "attendee": {
                "firstName": "Staffer",
                "lastName": "Testsalot",
                "badgeName": "Flagrant System Error",
                "address1": "123 Any Place",
                "address2": "",
                "city": "Countrytown",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "2125551212",
                "email": self.token.email,
                "birthdate": "1990-01-01",
            },
            "staff": {
                "department": self.department1.id,
                "title": "Something Cool",
                "twitter": "@twitstaff",
                "telegram": "@twitstaffagain",
                "shirtsize": self.shirt1.id,
                "specialSkills": "Something here",
                "specialFood": "no water please",
                "specialMedical": "alerigic to bandaids",
                "contactPhone": "4442223333",
                "contactName": "Test Testerson",
                "contactRelation": "Pet",
            },
            "priceLevel": {
                "id": self.price_150.id,
                "options": [
                    {"id": self.option_100_int.id, "value": 1},
                    {"id": self.option_shirt.id, "value": self.shirt1.id},
                ],
            },
            "event": self.event.name,
        }
        result = self.client.post(
            reverse("registration:add_new_staff"),
            json.dumps(body),
            content_type="application/json",
        )


class TestReturningStaff(StaffTestCase):
    def test_returning_staff(self):
        response = self.client.get(
            reverse("registration:returning_staff", args=("foo",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"not yet open", response.content)

    @freeze_time(timezone.now() - timedelta(days=20))
    def test_returning_staff_closed_upcoming(self):
        response = self.client.get(
            reverse("registration:returning_staff", args=("foo",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"not yet open", response.content)

    @freeze_time(timezone.now() + timedelta(days=20))
    def test_returning_staff_closed_ended(self):
        response = self.client.get(
            reverse("registration:returning_staff", args=("foo",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"has ended", response.content)

    def test_returning_staff_done(self):
        response = self.client.get(reverse("registration:returning_staff_done"))
        self.assertEqual(response.status_code, 200)


class TestInfoReturningStaff(StaffTestCase):
    def test_info_returning_staff_blank(self):
        result = self.client.get(reverse("registration:info_returning_staff"))
        self.assertEqual(result.status_code, 200)

    def test_info_returning_staff(self):
        session = self.client.session
        session["staff_id"] = self.staff.id
        session.save()
        result = self.client.get(reverse("registration:info_returning_staff"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["staff"], self.staff)
        self.assertEqual(result.context["paid_total"], 0)


class TestAddReturningStaff(StaffTestCase):
    @tag("square")
    def test_staff(self):
        # Failed lookup
        postData = {
            "email": "nottherightemail@somewhere.com",
            "token": self.staff.registrationToken,
        }
        response = self.client.post(
            reverse("registration:find_returning_staff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"success": False, "reason": "Staff matching query does not exist."},
        )

        # Regular staff reg
        postData = {"email": self.attendee.email, "token": self.staff.registrationToken}
        response = self.client.post(
            reverse("registration:find_returning_staff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_decoded = json.loads(response.content)
        self.assertEqual(response_decoded, {"message": "STAFF", "success": True})

        postData = {
            "attendee": {
                "id": self.attendee.id,
                "firstName": "Staffer",
                "lastName": "Testerson",
                "address1": "123 Somewhere St",
                "address2": "",
                "city": "Place",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "1112223333",
                "email": "apis@mailinator.com",
                "birthdate": "1990-01-01",
                "badgeName": "FluffyButz",
                "emailsOk": "true",
            },
            "staff": {
                "id": self.staff.id,
                "department": self.department1.id,
                "title": "Something Cool",
                "twitter": "@twitstaff",
                "telegram": "@twitstaffagain",
                "shirtsize": self.shirt1.id,
                "specialSkills": "Something here",
                "specialFood": "no water please",
                "specialMedical": "alerigic to bandaids",
                "contactPhone": "4442223333",
                "contactName": "Test Testerson",
                "contactRelation": "Pet",
            },
            "priceLevel": {
                "id": self.price_150.id,
                "options": [
                    {"id": self.option_100_int.id, "value": 1},
                    {"id": self.option_shirt.id, "value": self.shirt1.id},
                ],
            },
            "event": self.event.name,
        }
        response = self.client.post(
            reverse("registration:add_returning_staff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 150 + 100 - 45)
        discount = response.context["discount"]
        self.assertEqual(discount.codeName, "StaffDiscount")
        discountUsed = discount.used

        response = self.checkout("cnon:card-nonce-ok")
        self.assertEqual(response.status_code, 200)

        badge = Badge.objects.get(attendee=self.attendee, event=self.event)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount.codeName, "StaffDiscount")
        self.assertEqual(order.total, 150 + 100 - 45)
        self.assertEqual(order.orgDonation, 0)
        self.assertEqual(order.charityDonation, 0)
        self.assertEqual(order.discount.used, discountUsed + 1)

        response = self.client.get(reverse("registration:flush"))
        self.assertEqual(response.status_code, 200)

        # Staff zero-sum
        postData = {
            "email": self.attendee2.email,
            "token": self.staff2.registrationToken,
        }
        response = self.client.post(
            reverse("registration:find_returning_staff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_decoded = json.loads(response.content)
        self.assertEqual(response_decoded, {"message": "STAFF", "success": True})

        postData = {
            "attendee": {
                "id": self.attendee2.id,
                "firstName": "Staffer",
                "lastName": "Testerson",
                "address1": "123 Somewhere St",
                "address2": "",
                "city": "Place",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "1112223333",
                "email": "carissa.brittain@gmail.com",
                "birthdate": "1990-01-01",
                "badgeName": "FluffyButz",
                "emailsOk": "true",
            },
            "staff": {
                "id": self.staff2.id,
                "department": self.department2.id,
                "title": "Something Cool",
                "twitter": "@twitstaff",
                "telegram": "@twitstaffagain",
                "shirtsize": self.shirt1.id,
                "specialSkills": "Something here",
                "specialFood": "no water please",
                "specialMedical": "alerigic to bandaids",
                "contactPhone": "4442223333",
                "contactName": "Test Testerson",
                "contactRelation": "Pet",
            },
            "priceLevel": {
                "id": self.price_45.id,
                "options": [
                    {"id": self.option_conbook.id, "value": "true"},
                    {"id": self.option_shirt.id, "value": self.shirt1.id},
                ],
            },
            "event": self.event.name,
        }
        response = self.client.post(
            reverse("registration:add_returning_staff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45 - 45)
        discount = response.context["discount"]
        self.assertEqual(discount.codeName, "StaffDiscount")
        discountUsed = discount.used

        response = self.zero_checkout()
        self.assertEqual(response.status_code, 200)

        badge = Badge.objects.get(attendee=self.attendee2, event=self.event)
        orderItem = OrderItem.objects.get(badge=badge)
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount.codeName, "StaffDiscount")
        self.assertEqual(order.total, 0)
        self.assertEqual(order.discount.used, discountUsed + 1)

        response = self.client.get(reverse("registration:flush"))
        self.assertEqual(response.status_code, 200)


class TestStaffEmail(StaffTestCase):
    def test_get_staff_email(self):
        email = staff.get_staff_email()
        self.assertEqual(email, self.event.staffEmail)

    def test_get_staff_email_empty(self):
        self.event.staffEmail = ""
        self.event.save()
        email = staff.get_staff_email()
        self.assertEqual(email, settings.APIS_DEFAULT_EMAIL)


class TestAddReturningStaffBranches(StaffTestCase):
    """
    Test sad paths for add_returning_staff
    """

    def setUp(self):
        super().setUp()
        session = self.client.session
        session["staff_id"] = self.staff.id
        session.save()

    def _build_payload(self, **overrides):
        payload = {
            "attendee": {
                "id": self.attendee.id,
                "firstName": "Staffer",
                "lastName": "Testerson",
                "address1": "123 Somewhere St",
                "address2": "",
                "city": "Place",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "1112223333",
                "email": "apis@mailinator.com",
                "birthdate": "1990-01-01",
                "badgeName": "FluffyButz",
                "emailsOk": "true",
            },
            "staff": {
                "id": self.staff.id,
                "department": self.department1.id,
                "title": "Something Cool",
                "twitter": "@twitstaff",
                "telegram": "@twitstaffagain",
                "shirtsize": self.shirt1.id,
                "specialSkills": "Something here",
                "specialFood": "no water please",
                "specialMedical": "alerigic to bandaids",
                "contactPhone": "4442223333",
                "contactName": "Test Testerson",
                "contactRelation": "Pet",
            },
            "priceLevel": {
                "id": self.price_150.id,
                "options": [
                    {"id": self.option_100_int.id, "value": 1},
                    {"id": self.option_shirt.id, "value": self.shirt1.id},
                ],
            },
            "event": self.event.name,
        }
        # Shallow-merge overrides into nested dicts so tests can tweak
        # just a couple of keys without repeating the whole payload.
        for key, value in overrides.items():
            if (
                isinstance(value, dict)
                and key in payload
                and isinstance(payload[key], dict)
            ):
                payload[key].update(value)
            else:
                payload[key] = value
        return payload

    def _post(self, payload=None):
        body = (
            payload
            if isinstance(payload, str)
            else json.dumps(self._build_payload() if payload is None else payload)
        )
        return self.client.post(
            reverse("registration:add_returning_staff"),
            body,
            content_type="application/json",
        )

    def test_bad_json_returns_false(self):
        response = self._post("not valid json{{{")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": False})

    def test_uses_default_event_when_no_event_key(self):
        payload = self._build_payload()
        del payload["event"]
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_attendee_not_found(self):
        payload = self._build_payload(attendee={"id": 9999999})
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": False, "message": "Attendee not found"},
        )

    def test_missing_staff_id_in_session(self):
        session = self.client.session
        session.pop("staff_id", None)
        session.save()
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": False, "message": "Staff record not found"},
        )

    def test_staff_record_not_found(self):
        payload = self._build_payload(staff={"id": 9999999})
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": False, "message": "Staff record not found"},
        )

    def test_new_badge_created_when_none_exists(self):
        # attendee2 has a badge from setUp; delete it to hit the create branch
        Badge.objects.filter(attendee=self.attendee2, event=self.event).delete()
        session = self.client.session
        session["staff_id"] = self.staff2.id
        session.save()
        payload = self._build_payload(
            attendee={"id": self.attendee2.id},
            staff={"id": self.staff2.id},
        )
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        badges = Badge.objects.filter(attendee=self.attendee2, event=self.event)
        self.assertEqual(badges.count(), 1)
        self.assertEqual(badges.first().badgeName, "FluffyButz")

    def test_existing_badge_reused_and_renamed(self):
        # self.badge is created for self.attendee in StaffTestCase.setUp
        self.assertEqual(self.badge.badgeName, "DisStaff")
        payload = self._build_payload(attendee={"badgeName": "NewName"})
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        badges = Badge.objects.filter(attendee=self.attendee, event=self.event)
        self.assertEqual(badges.count(), 1)
        self.assertEqual(badges.first().badgeName, "NewName")

    def test_integrity_error_returns_409_and_rolls_back(self):
        original_first_name = self.attendee.firstName
        payload = self._build_payload(attendee={"firstName": "RolledBack"})
        with patch.object(
            staff, "staff_from_post_data", side_effect=IntegrityError("dup")
        ):
            response = self._post(payload)
        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertIn("conflicts", body["message"])
        # transaction.atomic should have rolled back the attendee.save()
        self.attendee.refresh_from_db()
        self.assertEqual(self.attendee.firstName, original_first_name)
        # and no OrderItem should have been created
        self.assertFalse(OrderItem.objects.filter(badge=self.badge).exists())

    def test_database_error_returns_503(self):
        with patch.object(
            staff, "staff_from_post_data", side_effect=DatabaseError("timeout")
        ):
            response = self._post()
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertIn("Please try again", body["message"])

    def test_no_discount_in_session_when_event_has_no_staff_discount(self):
        self.event.staffDiscount = None
        self.event.save()
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertNotIn("discount", self.client.session)

    def test_happy_path_populates_session(self):
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        session = self.client.session
        self.assertEqual(len(session["order_items"]), 1)
        self.assertEqual(session["discount"], self.staffdiscount.codeName)
