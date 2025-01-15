from tempfile import TemporaryDirectory
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from PIL import Image

from registration.models import (
    Attendee,
    AttendeeOptions,
    Badge,
    Event,
    Order,
    OrderItem,
    PriceLevel,
    PriceLevelOption,
)
from registration.views.common import getOptionsDict
from registration.tests.common import DEFAULT_EVENT_ARGS


class TestGetOptionsDict(TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_get_options_dict(self):
        event = Event(**DEFAULT_EVENT_ARGS)
        event.save()

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

        badge = Badge(
            attendee=attendee,
            event=event,
            badgeName="DisStaff"
        )
        badge.save()

        now = timezone.now()
        ten_days = timedelta(days=10)

        priceLevel = PriceLevel(
            name="Attendee",
            description="Hello",
            basePrice=1.00,
            startDate=now - ten_days,
            endDate=now + ten_days,
            public=True,
        )
        priceLevel.save()

        order = Order(
            total=100,
            billingType=Order.CREDIT,
            status=Order.COMPLETED,
            reference="CREDIT_ORDER_1",
        )
        order.save()

        order_item = OrderItem(
            order=order,
            badge=badge,
            priceLevel=priceLevel,
        )
        order_item.save()

        badge.refresh_from_db()

        options = getOptionsDict(badge.orderitem_set.all())
        self.assertEqual(len(options), 0)
        self.assertEqual(options, [])

        # Add a price level option
        pl_option = PriceLevelOption(
            optionName="Attendee",
            optionPrice=1.00,
            optionExtraType="int",
        )
        pl_option.save()

        attendee_option = AttendeeOptions(
            option=pl_option,
            orderItem=order_item,
            optionValue="1",
        )
        attendee_option.save()

        badge.refresh_from_db()

        options = getOptionsDict(badge.orderitem_set.all())
        self.assertEqual(len(options), 1)
        self.assertEqual(options, [{
            "name": pl_option.optionName,
            "type": pl_option.optionExtraType,
            "value": attendee_option.optionValue,
            "id": pl_option.id,
            "image": None,
        }])

        # Add an image to the price level option
        image = Image.new("RGB", (200, 100), "white")
        image_path = f"{self.tempdir.name}/testimage.jpg"
        image.save(image_path)
        pl_option.optionImage = image_path
        pl_option.save()

        badge.refresh_from_db()

        options = getOptionsDict(badge.orderitem_set.all())
        self.assertEqual(len(options), 1)
        self.assertEqual(options, [{
            "name": pl_option.optionName,
            "type": pl_option.optionExtraType,
            "value": attendee_option.optionValue,
            "id": pl_option.id,
            "image": image_path,
        }])
