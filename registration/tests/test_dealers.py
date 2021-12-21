from django.test import Client, TestCase
from django.urls import reverse
from freezegun import freeze_time

from registration.models import Event
from registration.tests.common import DEFAULT_EVENT_ARGS


class DealerTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()

        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()


class TestDealers(DealerTestCase):
    def test_addNewDealer_open(self) -> None:
        response = self.client.get(reverse("registration:newDealer"))
        self.assertEqual(response.status_code, 200)

    @freeze_time("2020-01-01")
    def test_addNewDealer_closed(self) -> None:
        response = self.client.get(reverse("registration:newDealer"))
        self.assertEqual(response.status_code, 200)
