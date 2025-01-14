import json
from datetime import datetime, timedelta

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
        self.token = TempToken.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            ignore_time_window=False,
        )
        self.token_used = TempToken.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            used=True,
            ignore_time_window=False,
        )
        self.token_expired = TempToken.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now - one_hour,
            ignore_time_window=False,
        )
        self.token_override = TempToken.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            ignore_time_window=True,
        )
        self.token_used_override = TempToken.objects.create(
            email="apis-staff-test@mailinator.com",
            validUntil=now + one_hour,
            used=True,
            ignore_time_window=True,
        )
        self.token_expired_override = TempToken.objects.create(
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


class TestFindStaff(TestCase):
    def test_find_staff_empty(self):
        response = self.client.post(reverse("registration:find_staff"))
        self.assertEqual(response.status_code, 400)

    def test_find_staff_404(self):
        body = {
            "email": "foo",
            "token": "bar",
        }
        response = self.client.post(
            reverse("registration:find_staff"),
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
        self.assertIn(b'<a href="/registration/">Back to Main Page</a>', response.content)

        self.event.websiteUrl = "https://example.com"
        self.event.save()

        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<a href="https://example.com">Back to Main Page</a>', response.content)

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
        self.assertIn(b'<a href="/registration/">Back to Main Page</a>', response.content)

        self.event.websiteUrl = "https://example.com"
        self.event.save()

        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<a href="https://example.com">Back to Main Page</a>', response.content)

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


class TestStaffIndex(StaffTestCase):
    def test_staff_index(self):
        response = self.client.get(reverse("registration:staff", args=("foo",)))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"not yet open", response.content)
        
    @freeze_time(timezone.now() - timedelta(days=20))
    def test_staff_index_closed_upcoming(self):
        response = self.client.get(reverse("registration:staff", args=("foo",)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"not yet open", response.content)

    @freeze_time(timezone.now() + timedelta(days=20))
    def test_staff_index_closed_ended(self):
        response = self.client.get(reverse("registration:staff", args=("foo",)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"has ended", response.content)

    def test_staff_done(self):
        response = self.client.get(reverse("registration:staff_done"))
        self.assertEqual(response.status_code, 200)


class TestInfoStaff(StaffTestCase):
    def test_info_staff_blank(self):
        result = self.client.get(reverse("registration:info_staff"))
        self.assertEqual(result.status_code, 200)

    def test_info_staff(self):
        session = self.client.session
        session["staff_id"] = self.staff.id
        session.save()
        result = self.client.get(reverse("registration:info_staff"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["staff"], self.staff)
        self.assertEqual(result.context["paid_total"], 0)


class TestAddStaff(StaffTestCase):
    @tag("square")
    def test_staff(self):
        # Failed lookup
        postData = {
            "email": "nottherightemail@somewhere.com",
            "token": self.staff.registrationToken,
        }
        response = self.client.post(
            reverse("registration:find_staff"),
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
            reverse("registration:find_staff"),
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
            reverse("registration:add_staff"),
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
            reverse("registration:find_staff"),
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
            reverse("registration:add_staff"),
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
