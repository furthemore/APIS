import logging
import time
import uuid
from datetime import datetime, timedelta
from unittest import skip

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.utils import timezone

from . import admin, payments
from .admin import OrderAdmin
from .models import *
from .pushy import PushyAPI

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)

tz = timezone.get_current_timezone()
now = timezone.now()
ten_days = timedelta(days=10)

DEFAULT_EVENT_ARGS = dict(
    default=True,
    name="Test Event 2050!",
    dealerRegStart=now - ten_days,
    dealerRegEnd=now + ten_days,
    staffRegStart=now - ten_days,
    staffRegEnd=now + ten_days,
    attendeeRegStart=now - ten_days,
    attendeeRegEnd=now + ten_days,
    onlineRegStart=now - ten_days,
    onlineRegEnd=now + ten_days,
    eventStart=now - ten_days,
    eventEnd=now + ten_days,
)


class DebugURLTrigger(TestCase):
    @override_settings(DEBUG=True)
    def test_debug(self):
        assert settings.DEBUG


class Index(TestCase):
    def setUp(self):
        self.client = Client()

    # unit tests skip methods that start with uppercase letters
    def TestIndex(self):
        response = self.client.get(reverse("registration:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the registration system")

    def TestIndexClosed(self):
        response = self.client.get(reverse("registration:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "is closed. If you have any")

    def TestIndexNoEvent(self):
        response = self.client.get(reverse("registration:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no default event was found")

    # this one runs
    def test_index(self):
        self.TestIndexNoEvent()
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()
        self.TestIndex()
        self.event.attendeeRegEnd = now - ten_days
        self.event.save()
        self.TestIndexClosed()


class OrdersTestCases(TestCase):
    def setUp(self):
        self.price_minor_25 = PriceLevel(
            name="Minor",
            description="I am a Minor!",
            basePrice=25.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
            isMinor=True,
        )
        self.price_45 = PriceLevel(
            name="Attendee",
            description="Some test description here",
            basePrice=45.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )
        self.price_90 = PriceLevel(
            name="Sponsor",
            description="Woot!",
            basePrice=90.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )
        self.price_150 = PriceLevel(
            name="Super",
            description="In the future",
            basePrice=150.00,
            startDate=now + ten_days,
            endDate=now + ten_days + ten_days,
            public=True,
        )
        self.price_235 = PriceLevel(
            name="Elite",
            description="ooOOOoooooo",
            basePrice=235.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=False,
        )
        self.price_675 = PriceLevel(
            name="Raven God",
            description="yay",
            basePrice=675.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=False,
            emailVIP=True,
            emailVIPEmails="apis@mailinator.com",
        )
        self.price_minor_25.save()
        self.price_45.save()
        self.price_90.save()
        self.price_150.save()
        self.price_235.save()
        self.price_675.save()

        self.department1 = Department(name="BestDept")
        self.department2 = Department(name="WorstDept")
        self.department1.save()
        self.department2.save()

        self.discount = Discount(
            codeName="FiveOff", amountOff=5.00, startDate=now, endDate=now + ten_days
        )
        self.onetimediscount = Discount(
            codeName="OneTime",
            percentOff=10,
            oneTime=True,
            startDate=now,
            endDate=now + ten_days,
        )
        self.staffdiscount = Discount(
            codeName="StaffDiscount",
            amountOff=45.00,
            startDate=now,
            endDate=now + ten_days,
        )
        self.dealerdiscount = Discount(
            codeName="DealerDiscount",
            amountOff=45.00,
            startDate=now,
            endDate=now + ten_days,
        )
        self.discount.save()
        self.onetimediscount.save()
        self.staffdiscount.save()
        self.dealerdiscount.save()

        self.shirt1 = ShirtSizes(name="Test_Large")
        self.shirt1.save()

        # TODO: shirt option type
        self.option_conbook = PriceLevelOption(
            optionName="Conbook", optionPrice=0.00, optionExtraType="bool"
        )
        self.option_shirt = PriceLevelOption(
            optionName="Shirt Size", optionPrice=0.00, optionExtraType="ShirtSizes"
        )
        self.option_100_int = PriceLevelOption(
            optionName="Something Pricy", optionPrice=100.00, optionExtraType="int"
        )

        self.option_conbook.save()
        self.option_shirt.save()
        self.option_100_int.save()

        self.price_45.priceLevelOptions.add(self.option_conbook)
        self.price_45.priceLevelOptions.add(self.option_shirt)
        self.price_90.priceLevelOptions.add(self.option_conbook)
        self.price_150.priceLevelOptions.add(self.option_conbook)
        self.price_150.priceLevelOptions.add(self.option_100_int)

        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.staffDiscount = self.staffdiscount
        self.event.dealerDiscount = self.dealerdiscount
        self.event.save()

        self.table_130 = TableSize(
            name="Booth",
            description="description here",
            chairMin=0,
            chairMax=1,
            tableMin=0,
            tableMax=1,
            partnerMin=0,
            partnerMax=1,
            basePrice=Decimal(130),
        )
        self.table_160 = TableSize(
            name="Booth",
            description="description here",
            chairMin=0,
            chairMax=1,
            tableMin=0,
            tableMax=1,
            partnerMin=0,
            partnerMax=2,
            basePrice=Decimal(160),
        )

        self.table_130.save()
        self.table_160.save()

        self.attendee_form_1 = {
            "firstName": "Tester",
            "lastName": "Testerson",
            "address1": "123 Somewhere St",
            "address2": "",
            "city": "Place",
            "state": "PA",
            "country": "US",
            "postal": "12345",
            "phone": "1112223333",
            "email": "apis@mailinator.org",
            "birthdate": "1990-01-01",
            "asl": "false",
            "badgeName": "FluffyButtz",
            "emailsOk": "true",
            "volunteer": "false",
            "volDepts": "",
            "surveyOk": "false",
        }
        self.attendee_form_2 = {
            "firstName": "Bea",
            "lastName": "Testerson",
            "address1": "123 Somewhere St",
            "address2": "Ste 300",
            "city": "Place",
            "state": "PA",
            "country": "US",
            "postal": "12345",
            "phone": "1112223333",
            "email": "apis@mailinator.com",
            "birthdate": "1990-01-01",
            "asl": "false",
            "badgeName": "FluffyButz",
            "emailsOk": "true",
            "volunteer": "false",
            "volDepts": "",
            "surveyOk": "false",
        }

        self.attendee_form_upgrade = self.attendee_form_1
        self.attendee_form_upgrade["firstName"] = "Upgrade"
        self.attendee_form_upgrade["lastName"] = "Me"
        self.attendee_form_upgrade["badgeName"] = "Upgrade Test"

        self.attendee_form_upgrade_checkout = {
            "billingData": {
                "address1": "Qui qui quasi amet",
                "address2": "Sunt voluptas dolori",
                "card_data": {
                    "billing_postal_code": "94044",
                    "card_brand": "VISA",
                    "digital_wallet_type": "NONE",
                    "exp_month": 12,
                    "exp_year": 2021,
                    "last_4": "1111",
                },
                "cc_firstname": "Whitney",
                "cc_lastname": "Thompson",
                "city": "Quam earum Nam dolor",
                "country": "FK",
                "email": "apis@mailinator.net",
                "nonce": "cnon:card-nonce-ok",
                "postal": "13271",
                "state": "",
            },
            "onsite": False,
            "orgDonation": "10",
        }

        self.attendee_upgrade = dict(
            firstName="Test",
            lastName="Upgrader",
            address1="123 Somewhere St",
            city="Place",
            state="PA",
            country="US",
            postalCode=12345,
            phone="1112223333",
            email="apis@mailinator.org",
            birthdate="1990-01-01",
        )

        self.client = Client()

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

    def add_to_cart(self, attendee, priceLevel, options):
        postData = {
            "attendee": attendee,
            "priceLevel": {"id": priceLevel.id, "options": options},
            "event": self.event.name,
        }

        response = self.client.post(
            reverse("registration:addToCart"),
            json.dumps(postData),
            content_type="application/json",
        )
        logging.info(response.content)
        self.assertEqual(response.status_code, 200)

    def zero_checkout(self):
        postData = {}
        response = self.client.post(
            reverse("registration:checkout"),
            json.dumps(postData),
            content_type="application/json",
        )
        return response

    def checkout(self, nonce, orgDonation="", charityDonation=""):
        postData = {
            "billingData": {
                "address1": "123 Any Street",
                "address2": "Apt 4",
                "card_data": {
                    "billing_postal_code": "12345",
                    "card_brand": "VISA",
                    "digital_wallet_type": "NONE",
                    "exp_month": 2,
                    "exp_year": 2020,
                    "last_4": "1111",
                },
                "cc_firstname": "Buffy",
                "cc_lastname": "Cleveland",
                "city": "39535",
                "country": "ST",
                "email": "apis@mailinator.net",
                "nonce": nonce,
                "postal": "45733",
                "state": "ID",
            },
            "charityDonation": charityDonation,
            "onsite": False,
            "orgDonation": orgDonation,
        }

        response = self.client.post(
            reverse("registration:checkout"),
            json.dumps(postData),
            content_type="application/json",
        )

        return response

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

        response = self.client.get(reverse("registration:cancelOrder"))
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
        self.assertEqual(
            response.content,
            '{"message": "That discount is not valid.", "success": false}',
        )

        postData = {"discount": "Bogus"}
        response = self.client.post(
            reverse("registration:discount"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            '{"message": "That discount is not valid.", "success": false}',
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

    def test_upgrade_index(self):
        guid = "ARSTBCESKFGHAIESTRK"
        response = self.client.get(reverse("registration:upgrade", args=[guid]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, guid)

    def test_infoUpgrade_bad_json(self):
        response = self.client.post(
            reverse("registration:infoUpgrade"),
            "notJSON-",
            content_type="application/json",
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"success": False})

    def test_infoUpgrade_wrong_token(self):
        # Failed lookup against infoUpgrade()
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
            reverse("registration:infoUpgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        badge.delete()
        attendee.delete()

    def test_infoUpgrade_wrong_email(self):
        # Failed lookup against infoUpgrade()
        attendee = Attendee(**self.attendee_upgrade)
        attendee.save()
        badge = Badge(attendee=attendee, event=self.event, badgeName="Test Upgrade")
        badge.save()
        post_data = {
            "email": "nottherightemail@somewhere.com",
            "token": badge.registrationToken,
        }
        response = self.client.post(
            reverse("registration:infoUpgrade"),
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
            reverse("registration:infoUpgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        badge.delete()
        attendee.delete()

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
            reverse("registration:infoUpgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("registration:findUpgrade"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["attendee"], attendee)
        self.assertEqual(response.context["badge"], badge)

        badge.delete()
        attendee.delete()

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

        # infoUpgrade()
        post_data = {
            "event": self.event.name,
            "email": badge.attendee.email,
            "token": badge.registrationToken,
        }
        response = self.client.post(
            reverse("registration:infoUpgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return badge, attendee

    def upgrade_add_and_checkout(self, price_level, form, badge, attendee):
        # addUpgrade()
        post_data = {
            "event": self.event.name,
            "badge": {"id": badge.id,},
            "attendee": {"id": attendee.id,},
            "priceLevel": {"id": price_level.id, "options": [],},
        }
        self.client.post(
            reverse("registration:addUpgrade"),
            json.dumps(post_data),
            content_type="application/json",
        )
        cart_response = self.client.get(reverse("registration:invoiceUpgrade"))

        checkout_response = self.client.post(
            reverse("registration:checkoutUpgrade"),
            json.dumps(form),
            content_type="application/json",
        )
        return cart_response, checkout_response

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

    def test_upgrade_zero(self):
        badge, attendee = self.setup_upgrade()
        cart, checkout = self.upgrade_add_and_checkout(
            self.price_45, self.attendee_form_upgrade_checkout, badge, attendee
        )
        self.assertEqual(checkout.status_code, 200)
        self.assertEqual(badge.effectiveLevel(), self.price_45)
        badge.delete()
        attendee.delete()

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
        self.assertEqual(response.content, "Staff matching query does not exist.")

        # Regular staff reg
        postData = {"email": attendee.email, "token": staff.registrationToken}
        response = self.client.post(
            reverse("registration:findStaff"),
            json.dumps(postData),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"message": "STAFF", "success": true}')

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
        self.assertEqual(response.content, '{"message": "STAFF", "success": true}')

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
        self.square_order.apiData = """
        {
            "payment": {
                "amount_money": {
                    "amount": 10000,
                    "currency": "USD"
                },
                "billing_address": {
                    "address_line_1": "Qui qui quasi amet ",
                    "address_line_2": "Sunt voluptas dolori",
                    "administrative_district_level_1": "",
                    "country": "FK",
                    "locality": "Quam earum Nam dolor",
                    "postal_code": "13271"
                },
                "card_details": {
                    "avs_status": "AVS_ACCEPTED",
                    "card": {
                        "bin": "411111",
                        "card_brand": "VISA",
                        "exp_month": 2,
                        "exp_year": 2021,
                        "fingerprint": "sq-1-DjCOZOf2iusD6RSZ3k7XEjS0rxZB24OMDtlav-NIIWmZazJHNYRRw8iK3DFQFSOfgA",
                        "last_4": "1111"
                    },
                    "cvv_status": "CVV_ACCEPTED",
                    "entry_method": "KEYED",
                    "statement_description": "SQ *DEFAULT TEST ACCOUNT",
                    "status": "CAPTURED"
                },
                "created_at": "2020-02-05T01:40:30.145Z",
                "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                "location_id": "MESD3N22DWR0F",
                "order_id": "WsfpRocSvcmpVJn6CmkkoTVrOhMZY",
                "processing_fee": [
                    {
                        "amount_money": {
                            "amount": 190,
                            "currency": "USD"
                        },
                        "effective_at": "2020-02-05T03:40:31.000Z",
                        "type": "INITIAL"
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
                    "bxMrD6jppRDNzVIDeou2qd24MCOZY_COroghYTDynfpIFO6RwXIP1sUxWa7eobswR1GOvYx1F"
                ],
                "refunded_money": {
                    "amount": 4700,
                    "currency": "USD"
                },
                "source_type": "CARD",
                "status": "COMPLETED",
                "total_money": {
                    "amount": 5500,
                    "currency": "USD"
                },
                "updated_at": "2020-02-06T11:28:31.883Z"
            },
            "refunds": [
                {
                    "amount_money": {
                        "amount": 1000,
                        "currency": "USD"
                    },
                    "created_at": "2020-02-06T10:59:34.855Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_ELsVHdtGxFzZxvBNr7MgWWReFNNvxV1DyZwH6IVnccG",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "8dUqeTvb3B6Bvphs9w5kLumZnJaZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "processing_fee": [
                        {
                            "amount_money": {
                                "amount": -29,
                                "currency": "USD"
                            },
                            "effective_at": "2020-02-05T03:40:31.000Z",
                            "type": "INITIAL"
                        }
                    ],
                    "reason": "testing second $10 refund",
                    "status": "COMPLETED",
                    "updated_at": "2020-02-06T10:59:38.223Z"
                },
                {
                    "amount_money": {
                        "amount": 500,
                        "currency": "USD"
                    },
                    "created_at": "2020-02-06T11:25:09.726Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_sqoyKz6Dz4PADiP8IemxSaHaNJg0lL8qDU3BBu4ojxF",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "EXBbGNCQlPUL5zbTlCOf56OspvJZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "reason": " [rechner]",
                    "status": "PENDING",
                    "updated_at": "2020-02-06T11:25:09.726Z"
                },
                {
                    "amount_money": {
                        "amount": 200,
                        "currency": "USD"
                    },
                    "created_at": "2020-02-06T11:28:31.883Z",
                    "id": "bxMrD6jppRDNzVIDeou2qd24MCOZY_COroghYTDynfpIFO6RwXIP1sUxWa7eobswR1GOvYx1F",
                    "location_id": "MESD3N22DWR0F",
                    "order_id": "e8Rnf1oG5Ruiv6CG0uTXksvvWhcZY",
                    "payment_id": "bxMrD6jppRDNzVIDeou2qd24MCOZY",
                    "reason": "Test $2 refund [rechner]",
                    "status": "PENDING",
                    "updated_at": "2020-02-06T11:28:31.883Z"
                }
            ]
        }
        """
        self.square_order.save()

        self.square_order_bad_id = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="SQUARE_ORDER_1",
        )
        self.square_order_bad_id.apiData = '{"payment" : { "id" : "bad-payment-id" }}'
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
        self.assertEquals(order.total, 0)
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
        self.assertEquals(order.total, 50)
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
            "amount_money": {"amount": 10000, "currency": settings.SQUARE_CURRENCY,},
            "reference_id": order.reference,
            "billing_address": {"postal_code": "94042",},
            "location_id": settings.SQUARE_LOCATION_ID,
        }
        square_response = payments.payments_api.create_payment(body)
        order.apiData = json.dumps(square_response.body)
        order.save()
        if nonce == "cnon:card-nonce-ok":
            self.assertTrue(square_response.is_success())
        time.sleep(2)
        return order

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
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )

        order = Order.objects.get(id=order.id)
        self.refunded_square_order = order
        self.assertEquals(order.total, 0)
        self.assertEqual(order.status, Order.REFUND_PENDING)

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
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )

        order = Order.objects.get(id=order.id)
        self.refunded_square_order = order
        self.assertEquals(order.total, 75)
        self.assertEquals(order.charityDonation, 20)
        self.assertEquals(order.orgDonation, 20)
        self.assertEquals(order.status, Order.REFUND_PENDING)

        form_data = {
            "amount": "50",
            "reason": "2nd $50 refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )
        order = Order.objects.get(id=order.id)
        self.assertContains(
            response,
            "Refunded order has caused charity and organization donation amounts to reset.",
        )
        self.refunded_square_order = order
        self.assertEquals(order.total, 25)
        self.assertEquals(order.charityDonation, 25)
        self.assertEquals(order.orgDonation, 0)
        self.assertEqual(order.status, Order.REFUND_PENDING)

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
            "Error while loading JSON from apiData field for this order: No JSON object could be decoded",
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
            response, "INVALID_REQUEST_ERROR - NOT_FOUND",
        )
        self.assertContains(response, "There was a problem")

        # Test against captured & failed transactions:
        order = self.create_square_order(nonce="cnon:card-nonce-declined")
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse("admin:registration_order_change", args=(order.id,)),
        )
        order = Order.objects.get(id=order.id)
        self.assertEquals(order.status, order.FAILED)

        order = self.create_square_order(autocomplete=False)
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse("admin:registration_order_change", args=(order.id,)),
        )
        order = Order.objects.get(id=order.id)
        self.assertEquals(order.status, order.CAPTURED)

        # Create refund to test admin form data against:
        order = self.create_square_order()
        form_data = {
            "amount": order.total,
            "reason": "full refund test",
        }
        form = OrderAdmin.RefundForm(data=form_data)

        self.assertTrue(form.is_valid())
        response = self.client.post(
            reverse("admin:order_refund", args=(order.id,)), form_data, follow=True,
        )

        order = Order.objects.get(id=order.id)
        response = self.client.get(
            reverse("admin:order_refresh", args=(order.id,)), follow=True
        )
        self.assertRedirects(
            response, reverse("admin:registration_order_change", args=(order.id,)),
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
        self.assertEquals(cash_drawer.tendered, 0)
        self.assertEquals(cash_drawer.user, self.admin_user)
        cash_drawer.delete()


class TestTwoFactorAdmin(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user("john", "lennon@thebeatles.com", "john")
        self.user_2 = User.objects.create_superuser("admin", "admin@host", "admin")
        self.user_1.staff_member = True
        self.user_1.save()
        self.user_2.save()

    def test_disable_two_factor(self):
        query_set = [self.user_1, self.user_2]
        admin.disable_two_factor(None, None, query_set)


class Onsite(TestCase):
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

        self.client = Client()

    def test_onsite_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("registration:onsiteAdmin"), follow=True)
        self.assertRedirects(
            response,
            "/admin/login/?next={0}".format(reverse("registration:onsiteAdmin")),
        )

    def test_onsite_admin_required(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="john", password="john"))
        response = self.client.get(reverse("registration:onsiteAdmin"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "are not authorized to access this page")
        self.client.logout()

    def test_onsite_admin(self):
        self.client.logout()
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(reverse("registration:onsiteAdmin"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["errors"]), 0)
        self.assertEqual(len(response.context["terminals"]), 1)

        self.terminal.delete()
        response = self.client.get(reverse("registration:onsiteAdmin"))
        self.assertEqual(response.status_code, 200)
        errors = [e["code"] for e in response.context["errors"]]
        # import pdb; pdb.set_trace()
        self.assertTrue("ERROR_NO_TERMINAL" in errors)

        self.terminal = Firebase(token="test", name="Terminal 1")
        self.terminal.save()
        response = self.client.get(
            reverse("registration:onsiteAdmin"), {"search": "doesntexist"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.context.keys())
        self.assertEqual(len(response.context["results"]), 0)

        self.client.logout()


class TestPushyAPI(TestCase):
    def test_sendPushNotification(self):
        PushyAPI.sendPushNotification("data", "to", None)
