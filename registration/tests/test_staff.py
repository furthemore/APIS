import json
from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import tag
from django.urls import reverse

from registration.models import *
from registration.tests.common import OrdersTestCase

tz = timezone.get_current_timezone()
now = timezone.now()
one_hour = timedelta(hours=1)
one_day = timedelta(days=1)
ten_days = timedelta(days=10)


class StaffTestCase(TestCase):
    def setUp(self):
        self.token = TempToken.objects.create(
            email="apis-staff-test@mailinator.com", validUntil=now + one_hour
        )
        self.token_used = TempToken.objects.create(
            email="apis-staff-test@mailinator.com", validUntil=now + one_hour, used=True
        )
        self.token_expired = TempToken.objects.create(
            email="apis-staff-test@mailinator.com", validUntil=now - one_hour
        )

        self.event = Event.objects.create(
            default=True,
            name="Test Event 2020!",
            dealerRegStart=now - ten_days,
            dealerRegEnd=now + ten_days,
            staffRegStart=now - ten_days,
            staffRegEnd=now + ten_days,
            attendeeRegStart=now - ten_days,
            attendeeRegEnd=now + ten_days,
            onsiteRegStart=now - ten_days,
            onsiteRegEnd=now + ten_days,
            eventStart=now + one_day,
            eventEnd=now + ten_days,
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
    def test_new_staff(self):
        response = self.client.get(reverse("registration:new_staff", args=("foobar",)))
        self.assertEqual(response.status_code, 200)


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


class TestAddNewStaff(OrdersTestCase):
    def setUp(self):
        super().setUp()
        self.token = TempToken.objects.create(
            email="apis-staff-test@mailinator.com", validUntil=now + one_hour
        )
        self.token_used = TempToken.objects.create(
            email="apis-staff-test@mailinator.com", validUntil=now + one_hour, used=True
        )
        self.token_expired = TempToken.objects.create(
            email="apis-staff-test@mailinator.com", validUntil=now - one_hour
        )

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


class TestAddStaff(OrdersTestCase):
    @tag("square")
    def test_staff(self):
        attendee = Attendee(
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
        attendee.save()
        staff = Staff(attendee=attendee, event=self.event)
        staff.save()
        badge = Badge(attendee=attendee, event=self.event, badgeName="DisStaff")
        badge.save()
        attendee2 = Attendee(
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
        attendee2.save()
        staff2 = Staff(attendee=attendee2, event=self.event)
        staff2.save()
        badge2 = Badge(attendee=attendee2, event=self.event, badgeName="AnotherStaff")
        badge2.save()

        # Failed lookup
        postData = {
            "email": "nottherightemail@somewhere.com",
            "token": staff.registrationToken,
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
        postData = {"email": attendee.email, "token": staff.registrationToken}
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
                "id": attendee.id,
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
                "id": staff.id,
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

        badge = Badge.objects.get(attendee=attendee, event=self.event)
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
        postData = {"email": attendee2.email, "token": staff2.registrationToken}
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
                "id": attendee2.id,
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
                "id": staff2.id,
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

        badge = Badge.objects.get(attendee=attendee2, event=self.event)
        orderItem = OrderItem.objects.get(badge=badge)
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount.codeName, "StaffDiscount")
        self.assertEqual(order.total, 0)
        self.assertEqual(order.discount.used, discountUsed + 1)

        response = self.client.get(reverse("registration:flush"))
        self.assertEqual(response.status_code, 200)
