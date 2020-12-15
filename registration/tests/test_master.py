import io
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.test.utils import override_settings
from mock import patch

from registration.models import *
from registration.pushy import PushyAPI, PushyError
from registration.tests.common import *


class DebugURLTrigger(TestCase):
    @override_settings(DEBUG=True)
    def test_debug(self):
        self.assertTrue(settings.DEBUG)


class TestAttendeeCheckout(OrdersTestCase):
    def test_get_prices(self):
        response = self.client.get(reverse("registration:pricelevels"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 3)
        basic = [item for item in result if item["name"] == "Attendee"]
        self.assertEqual(basic[0]["base_price"], "45.00")
        special = [item for item in result if item["name"] == "Special"]
        self.assertEqual(special, [])
        minor = [item for item in result if item["name"] == "Minor"]
        self.assertEqual(minor.__len__(), 1)

    def test_get_adult_prices(self):
        response = self.client.get(reverse("registration:adultpricelevels"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        basic = [item for item in result if item["name"] == "Attendee"]
        self.assertEqual(basic[0]["base_price"], "45.00")
        special = [item for item in result if item["name"] == "Special"]
        self.assertEqual(special, [])
        minor = [item for item in result if item["name"] == "Minor"]
        self.assertEqual(minor, [])

    def test_get_accompanied_price_levels(self):
        response = self.client.get(reverse("registration:accompaniedpricelevels"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["base_price"], "0.00")
        self.assertEqual(result[0]["name"], "Accompanied")

    def test_get_minor_price_levels(self):
        response = self.client.get(reverse("registration:minorpricelevels"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["base_price"], "25.00")
        self.assertEqual(result[0]["name"], "Minor")

    def get_free_price_levels(self):
        response = self.client.get(reverse("registration:freepricelevels"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["base_price"], "0.00")
        self.assertEqual(result[0]["name"], "Free")

    # Single transaction tests
    # =======================================================================

    def test_checkout(self):
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(self.attendee_form_2, self.price_45, options)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        response = self.checkout("cnon:card-nonce-ok", "20", "10")
        self.assertEqual(response.status_code, 200)

        # Check that user was successfully saved
        attendee = Attendee.objects.get(firstName="Bea")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)

        order = badge.getOrder()
        self.assertEqual(order.discount, None)
        self.assertEqual(order.total, 45 + 10 + 20)
        self.assertEqual(attendee.postalCode, order.billingPostal)
        self.assertEqual(order.orgDonation, 20)
        self.assertEqual(order.charityDonation, 10)

        # Square should overwrite this with a random sandbox value
        self.assertNotEqual(order.lastFour, "1111")
        self.assertNotEqual(order.lastFour, "")
        self.assertNotEqual(order.notes, "")
        self.assertNotEqual(order.apiData, "")

        # Clean up
        badge.delete()

    def test_zero_checkout(self):
        # TODO
        pass

    def assert_square_error(self, nonce, error):
        self.add_to_cart(self.attendee_form_2, self.price_45, [])
        result = self.checkout(nonce)
        self.assertEqual(result.status_code, 400)

        message = result.json()
        error_codes = [err["code"] for err in message["reason"]["errors"]]
        logger.error(error_codes)
        self.assertIn(error, error_codes)

        # Ensure a badge wasn't created
        self.assertEqual(Attendee.objects.filter(firstName="Bea").count(), 0)

    def test_bad_cvv(self):
        self.assert_square_error("cnon:card-nonce-rejected-cvv", "CVV_FAILURE")

    def test_bad_postalcode(self):
        self.assert_square_error(
            "cnon:card-nonce-rejected-postalcode", "ADDRESS_VERIFICATION_FAILURE"
        )

    def test_bad_expiration(self):
        self.assert_square_error(
            "cnon:card-nonce-rejected-expiration", "INVALID_EXPIRATION"
        )

    def test_card_declined(self):
        self.assert_square_error("cnon:card-nonce-declined", "GENERIC_DECLINE")

    def test_full_single_order(self):
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]

        self.add_to_cart(self.attendee_form_1, self.price_45, options)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        response = self.client.get(reverse("registration:cancel_order"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Tester").count(), 0)
        self.assertEqual(Badge.objects.filter(badgeName="FluffyButz").count(), 0)
        self.assertEqual(PriceLevel.objects.filter(id=self.price_45.id).count(), 1)

    def test_vip_checkout(self):
        self.add_to_cart(self.attendee_form_2, self.price_675, [])

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 675)

        response = self.checkout("cnon:card-nonce-ok", "1", "10")
        self.assertEqual(response.status_code, 200)

        attendee = Attendee.objects.get(firstName="Bea")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount, None)
        self.assertEqual(order.total, 675 + 11)
        self.assertEqual(attendee.postalCode, order.billingPostal)
        self.assertEqual(order.orgDonation, 1.00)
        self.assertEqual(order.charityDonation, 10.00)

    def test_discount(self):
        options = [
            {"id": self.option_conbook.id, "value": "true"},
            {"id": self.option_shirt.id, "value": self.shirt1.id},
        ]
        self.add_to_cart(self.attendee_form_2, self.price_45, options)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        postData = {"discount": "OneTime"}
        response = self.client.post(
            reverse("registration:discount"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 40.50)

        response = self.checkout("cnon:card-nonce-ok", "1", "10")
        self.assertEqual(response.status_code, 200)

        discount = Discount.objects.get(codeName="OneTime")
        self.assertEqual(discount.used, 1)

        postData = {"discount": "OneTime"}
        response = self.client.post(
            reverse("registration:discount"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json, {"message": "That discount is not valid.", "success": False},
        )

        postData = {"discount": "Bogus"}
        response = self.client.post(
            reverse("registration:discount"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json, {"message": "That discount is not valid.", "success": False},
        )

    def test_discount_zero_sum(self):
        options = [{"id": self.option_conbook.id, "value": "true"}]
        self.add_to_cart(self.attendee_form_2, self.price_45, options)

        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        postData = {"discount": "StaffDiscount"}
        response = self.client.post(
            reverse("registration:discount"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("registration:cart"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 0)

        discount = Discount.objects.get(codeName="StaffDiscount")
        discountUsed = discount.used

        response = self.zero_checkout()
        self.assertEqual(response.status_code, 200)

        discount = Discount.objects.get(codeName="StaffDiscount")
        self.assertEqual(discount.used, discountUsed + 1)

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
            reverse("registration:findStaff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Staff matching query does not exist.")

        # Regular staff reg
        postData = {"email": attendee.email, "token": staff.registrationToken}
        response = self.client.post(
            reverse("registration:findStaff"),
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
            reverse("registration:addStaff"),
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
        orderItem = OrderItem.objects.get(badge=badge)
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
            reverse("registration:findStaff"),
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
            reverse("registration:addStaff"),
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

    def test_dealer(self):
        dealer_pay = {
            "attendee": {
                "firstName": "Dealer",
                "lastName": "Testerson",
                "address1": "123 Somewhere St",
                "address2": "",
                "city": "Place",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "1112223333",
                "email": "testerson@mailinator.org",
                "birthdate": "1990-01-01",
                "badgeName": "FluffyButz",
                "emailsOk": "true",
                "surveyOk": "true",
            },
            "dealer": {
                "businessName": "Something Creative",
                "website": "http://www.something.com",
                "logo": "",
                "license": "jkah9435kd",
                "power": False,
                "wifi": False,
                "wall": True,
                "near": "Someone",
                "far": "Someone Else",
                "description": "Stuff for sale",
                "tableSize": self.table_130.id,
                "chairs": 1,
                "partners": [],
                "tables": 0,
                "reception": True,
                "artShow": False,
                "charityRaffle": "Some stuff",
                "agreeToRules": True,
                "breakfast": True,
                "switch": False,
                "buttonOffer": "Buttons",
                "asstbreakfast": False,
            },
            "event": self.event.name,
        }

        response = self.client.post(
            reverse("registration:addNewDealer"),
            json.dumps(dealer_pay),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        dealer_free = {
            "attendee": {
                "firstName": "Free",
                "lastName": "Testerson",
                "address1": "123 Somewhere St",
                "address2": "",
                "city": "Place",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "1112223333",
                "email": "testerson@mailinator.org",
                "birthdate": "1990-01-01",
                "badgeName": "FluffyNutz",
                "emailsOk": "true",
                "surveyOk": "true",
            },
            "dealer": {
                "businessName": "Something Creative",
                "website": "http://www.something.com",
                "logo": "",
                "license": "jkah9435kd",
                "power": True,
                "wifi": True,
                "wall": True,
                "near": "Someone",
                "far": "Someone Else",
                "description": "Stuff for sale",
                "tableSize": self.table_130.id,
                "chairs": 1,
                "partners": [],
                "tables": 0,
                "reception": True,
                "artShow": False,
                "charityRaffle": "Some stuff",
                "agreeToRules": True,
                "breakfast": True,
                "switch": False,
                "buttonOffer": "Buttons",
                "asstbreakfast": False,
            },
            "event": self.event.name,
        }

        response = self.client.post(
            reverse("registration:addNewDealer"),
            json.dumps(dealer_free),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        dealer_partners = {
            "attendee": {
                "firstName": "Dealz",
                "lastName": "Testerson",
                "address1": "123 Somewhere St",
                "address2": "",
                "city": "Place",
                "state": "PA",
                "country": "US",
                "postal": "12345",
                "phone": "1112223333",
                "email": "testerson@mailinator.org",
                "birthdate": "1990-01-01",
                "badgeName": "FluffyGutz",
                "emailsOk": "true",
                "surveyOk": "true",
            },
            "dealer": {
                "businessName": "Something Creative",
                "website": "http://www.something.com",
                "logo": "",
                "license": "jkah9435kd",
                "power": True,
                "wifi": True,
                "wall": True,
                "near": "Someone",
                "far": "Someone Else",
                "description": "Stuff for sale",
                "tableSize": self.table_160.id,
                "partners": [
                    {
                        "name": "Someone",
                        "email": "someone@here.com",
                        "license": "temporary",
                        "tempLicense": True,
                    },
                    {"name": "", "email": "", "license": "", "tempLicense": False},
                ],
                "chairs": 1,
                "tables": 0,
                "reception": False,
                "artShow": False,
                "charityRaffle": "Some stuff",
                "agreeToRules": True,
                "breakfast": True,
                "switch": False,
                "buttonOffer": "Buttons",
                "asstbreakfast": False,
            },
            "event": self.event.name,
        }

        response = self.client.post(
            reverse("registration:addNewDealer"),
            json.dumps(dealer_partners),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        attendee = Attendee.objects.get(firstName="Dealer")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertEqual(badge.badgeName, "FluffyButz")
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 0)
        dealer = Dealer.objects.get(attendee=attendee)
        self.assertNotEqual(dealer, None)

        attendee = Attendee.objects.get(firstName="Dealz")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertEqual(badge.badgeName, "FluffyGutz")
        self.assertNotEqual(badge.registeredDate, None)
        dealer = Dealer.objects.get(attendee=attendee)
        self.assertNotEqual(dealer, None)

        attendee = Attendee.objects.get(firstName="Free")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertEqual(badge.badgeName, "FluffyNutz")
        self.assertNotEqual(badge.registeredDate, None)
        dealer = Dealer.objects.get(attendee=attendee)
        self.assertNotEqual(dealer, None)

        response = self.client.get(reverse("registration:flush"))
        self.assertEqual(response.status_code, 200)

        # Dealer
        attendee = Attendee.objects.get(firstName="Dealer")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        postData = {"token": dealer.registrationToken, "email": attendee.email}
        response = self.client.post(
            reverse("registration:findDealer"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        dealer_pay["attendee"]["id"] = attendee.id
        dealer_pay["dealer"]["id"] = dealer.id
        dealer_pay["priceLevel"] = {"id": self.price_45.id, "options": []}

        response = self.client.post(
            reverse("registration:addDealer"),
            json.dumps(dealer_pay),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("registration:invoiceDealer"))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]


class LookupTestCases(TestCase):
    def setUp(self):
        shirt1 = ShirtSizes(name="Test_Large")
        shirt2 = ShirtSizes(name="Test_Small")
        shirt1.save()
        shirt2.save()

        dept1 = Department(name="Reg", volunteerListOk=True)
        dept2 = Department(name="Safety")
        dept3 = Department(name="Charity", volunteerListOk=True)
        dept1.save()
        dept2.save()
        dept3.save()

    def test_shirts(self):
        client = Client()
        response = client.get(reverse("registration:shirtsizes"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        large = [item for item in result if item["name"] == "Test_Large"]
        self.assertNotEqual(large, [])

    def test_departments(self):
        client = Client()
        response = client.get(reverse("registration:departments"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        reg = [item for item in result if item["name"] == "Reg"]
        self.assertNotEqual(reg, [])
        safety = [item for item in result if item["name"] == "Safety"]
        self.assertEqual(safety, [])


class TestPushyAPI(TestCase):
    @patch("urllib.request.urlopen")
    def test_sendPushNotification(self, mock_urlopen):
        data = {"data": "some cool message here"}
        PushyAPI.sendPushNotification(data, "to", None)
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_sendPushNotification_sad_path(self, mock_urlopen):
        data = {"data": "some cool message here"}
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.pushy.me/push",
            400,
            "Pushy didn't like that!",
            None,
            io.StringIO(),
        )
        with self.assertRaises(PushyError):
            PushyAPI.sendPushNotification(data, "to", None)
        mock_urlopen.assert_called_once()
