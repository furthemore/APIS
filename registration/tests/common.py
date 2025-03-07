import json
import logging
import uuid
from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from registration.models import *

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)

tz = timezone.get_current_timezone()
now = timezone.now()
ten_days = timedelta(days=10)
one_day = timedelta(days=1)

DEFAULT_EVENT_ARGS = dict(
    default=True,
    name="Test Event 2050!",
    dealerRegStart=now - ten_days,
    dealerRegEnd=now + ten_days,
    staffRegStart=now - ten_days,
    staffRegEnd=now + ten_days,
    attendeeRegStart=now - ten_days,
    attendeeRegEnd=now + ten_days,
    onsiteRegStart=now - ten_days,
    onsiteRegEnd=now + ten_days,
    eventStart=now - ten_days,
    eventEnd=now + ten_days,
)

TEST_SIGNATURE_SVG = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+PCFET0NUWVBFIHN2ZyBQVUJMSUMgIi0vL1czQy8vRFREIFNWRyAxLjEvL0VOIiAiaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkIj48c3ZnIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgdmVyc2lvbj0iMS4xIiB3aWR0aD0iNjI3IiBoZWlnaHQ9IjkwIj48cGF0aCBzdHJva2UtbGluZWpvaW49InJvdW5kIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlPSJyZ2IoODUsIDg1LCA4NSkiIGZpbGw9Im5vbmUiIGQ9Ik0gMSA1NSBjIDAuMDUgLTAuMjEgMS4yIC04LjU5IDMgLTEyIGMgNC4yIC03Ljk1IDEwLjE2IC0xNi41NSAxNiAtMjQgYyAzLjcyIC00Ljc1IDguNDYgLTkuMjkgMTMgLTEzIGMgMi41NCAtMi4wOCA2LjE1IC0zLjk4IDkgLTUgYyAxLjM4IC0wLjQ5IDMuNzkgLTAuNjEgNSAwIGMgMi4yNCAxLjEyIDYuMzYgMy42IDcgNiBjIDMgMTEuMzEgNC40OSAyOC4zNiA2IDQzIGMgMC44NyA4LjQ0IDAuMjcgMTYuNzcgMSAyNSBjIDAuMjcgMy4wMyAxLjAzIDYuMjcgMiA5IGMgMC42MiAxLjczIDEuNjYgNC44MiAzIDUgYyA2LjE5IDAuODMgMTguMjMgMC41MyAyNyAtMSBjIDI1LjI5IC00LjQyIDQ5LjY3IC0xMS40NCA3NiAtMTcgYyAxMS4zNCAtMi4zOSAyMS44MSAtNC40IDMzIC02IGMgNS4zNSAtMC43NiAxMC41IC0wLjg2IDE2IC0xIGMgNy41NCAtMC4yIDE1LjIxIC0wLjk0IDIyIDAgYyA0LjU5IDAuNjQgOS40NyAyLjk5IDE0IDUgYyA0LjUgMiA4Ljc0IDUuMiAxMyA3IGMgMS43NiAwLjc0IDMuOTggMC45MyA2IDEgYyA4LjI5IDAuMjcgMTYuNjggMC41NSAyNSAwIGMgNi43MyAtMC40NSAyMCAtMyAyMCAtMyIvPjxwYXRoIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2U9InJnYig4NSwgODUsIDg1KSIgZmlsbD0ibm9uZSIgZD0iTSAyMDUgMzggYyAwLjI1IDAgOS4zOCAwLjQ5IDE0IDAgYyA4LjAyIC0wLjg0IDE1LjgzIC0zLjIzIDI0IC00IGMgMTMuNDQgLTEuMjYgMjYuMjEgLTEuODQgNDAgLTIgYyA0NC4wOCAtMC41MiA4NC44OCAtMS43NSAxMjggMCBjIDIzLjQgMC45NSA0NS41NiA0LjMgNjkgOCBjIDI4LjUzIDQuNSA1NS4wMyAxMC4xNyA4MyAxNiBjIDQuNSAwLjk0IDguNTMgMy4xNSAxMyA0IGMgMTYuNjMgMy4xNyA1MCA4IDUwIDgiLz48L3N2Zz4="

TEST_ATTENDEE_ARGS = dict(
    firstName="Test",
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

DEFAULT_VENUE_ARGS = dict(
    name="MegaCenter Conference Hotel",
    address="123 Somewhere St",
    city="Place",
    state="VA",
    country="US",
    postalCode=12345,
)

TEST_TABLE_ARGS = dict(
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

TEST_DEALER_ARGS = {
    "businessName": "Something Creative",
    "website": "http://www.something.com",
    "license": "jkah9435kd",
    "nearTo": "Someone",
    "farFrom": "Someone Else",
    "description": "Stuff for sale",
    "chairs": 1,
    "tables": 0,
    "reception": True,
    "artShow": False,
    "charityRaffle": "Some stuff",
    "agreeToRules": True,
    "breakfast": True,
    "buttonOffer": "Buttons",
    "asstBreakfast": False,
}

TEST_DEALER_ASST_ARGS = {
    "name": "Foobian the First",
    "email": "dealer-assistant@mailinator.org",
    "license": "N/A",
}


class OrdersTestCase(TestCase):
    def setUp(self):
        self.price_free = PriceLevel(
            name="Free",
            description="I am Free!!",
            basePrice=0.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=False,
            isMinor=True,
            available_to_attendee=True,
        )
        self.price_minor_25 = PriceLevel(
            name="Minor",
            description="I am a Minor!",
            basePrice=25.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=False,
            isMinor=True,
            available_to_attendee=True,
        )
        self.price_accompanied_0 = PriceLevel(
            name="Accompanied",
            description="I am an Accompanied minor!",
            basePrice=0,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=False,
            isMinor=True,
            available_to_attendee=True,
        )
        self.price_minor_35 = PriceLevel(
            name="Minor",
            description="I am a public Minor!",
            basePrice=35.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
            isMinor=True,
            available_to_attendee=True,
        )
        self.price_45 = PriceLevel(
            name="Attendee",
            description="Some test description here",
            basePrice=45.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
            available_to_attendee=True,
        )
        self.price_90 = PriceLevel(
            name="Sponsor",
            description="Woot!",
            basePrice=90.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
            available_to_attendee=True,
        )
        self.price_150 = PriceLevel(
            name="Super",
            description="In the future",
            basePrice=150.00,
            startDate=now + ten_days,
            endDate=now + ten_days + ten_days,
            public=True,
            available_to_attendee=True,
        )
        self.price_235 = PriceLevel(
            name="Elite",
            description="ooOOOoooooo",
            basePrice=235.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=False,
            available_to_attendee=True,
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
            available_to_attendee=True,
        )
        self.price_free.save()
        self.price_minor_25.save()
        self.price_accompanied_0.save()
        self.price_minor_35.save()
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
            "signature_svg": TEST_SIGNATURE_SVG,
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
            "signature_svg": TEST_SIGNATURE_SVG,
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
                "source_id": "cnon:card-nonce-ok",
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

    def add_to_cart(self, attendee, priceLevel, options):
        postData = {
            "attendee": attendee,
            "priceLevel": {"id": priceLevel.id, "options": options},
            "event": self.event.name,
        }

        response = self.client.post(
            reverse("registration:add_to_cart"),
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
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        return response

    def checkout(self, token, orgDonation="", charityDonation="", onsite=False):
        postData = {
            "billingData": {},
            "charityDonation": charityDonation,
            "onsite": False,
            "orgDonation": orgDonation,
        }

        if not onsite:
            postData["billingData"] = {
                "address1": "123 Any Street",
                "address2": "Apt 4",
                "cc_firstname": "Buffy",
                "cc_lastname": "Cleveland",
                "city": "39535",
                "country": "ST",
                "email": "apis@mailinator.net",
                "source_id": token,
                "postal": "45733",
                "state": "ID",
            }

        response = self.client.post(
            reverse("registration:checkout"),
            json.dumps(postData),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )

        return response
