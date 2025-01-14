from django.http import HttpRequest
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from freezegun import freeze_time

from registration.models import Attendee, Dealer, DealerAsst, Event
from registration.tests.common import (
    DEFAULT_EVENT_ARGS,
    TEST_ATTENDEE_ARGS,
    TEST_DEALER_ARGS,
    TEST_DEALER_ASST_ARGS,
)
from registration.views import ordering


class DealerTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.assistant.refresh_from_db()

    @classmethod
    def setUpTestData(cls):
        cls.event = Event(**DEFAULT_EVENT_ARGS)
        cls.event.save()

        cls.dealer = Dealer(**TEST_DEALER_ARGS)
        cls.dealer.event = cls.event
        cls.dealer.save()

        cls.attendee = Attendee(**TEST_ATTENDEE_ARGS)
        cls.attendee.save()

        cls.assistant = DealerAsst(**TEST_DEALER_ASST_ARGS)
        cls.assistant.dealer = cls.dealer
        cls.assistant.save()


class TestDealers(DealerTestCase):
    def test_dealers(self):
        response = self.client.get(reverse("registration:dealers", args=("FOOBAR",)))
        self.assertEqual(response.status_code, 200)

    def test_thanksDealer(self):
        response = self.client.get(reverse("registration:thanks_dealer"))
        self.assertEqual(response.status_code, 200)

    def test_doneDealer(self):
        response = self.client.get(reverse("registration:done_dealer"))
        self.assertEqual(response.status_code, 200)

    def test_addNewDealer_open(self) -> None:
        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"not yet open", response.content)

    @freeze_time(timezone.now() - timedelta(days=20))
    def test_addNewDealer_closed_upcoming(self) -> None:
        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"not yet open", response.content)
        self.assertIn(b'<a href="/registration/">Back to Main Page</a>', response.content)

        self.event.websiteUrl = "https://example.com"
        self.event.save()

        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<a href="https://example.com">Back to Main Page</a>', response.content)

    @freeze_time(timezone.now() + timedelta(days=20))
    def test_addNewDealer_closed_ended(self) -> None:
        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"has ended", response.content)
        self.assertIn(b'<a href="/registration/">Back to Main Page</a>', response.content)

        event = Event.objects.get(default=True)
        event.websiteUrl = "https://example.com"
        event.save()

        response = self.client.get(reverse("registration:new_dealer"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<a href="https://example.com">Back to Main Page</a>', response.content)

    def test_find_dealer_to_add_assistant(self):
        response = self.client.get(
            reverse("registration:find_dealer_to_add_assistant", args=("FOOBAR",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FOOBAR", response.content)

    def test_dealerAsst(self):
        response = self.client.get(
            reverse("registration:dealer_asst", args=("FOOBAR",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FOOBAR", response.content)

    def test_doneAsstDealer(self):
        response = self.client.get(reverse("registration:done_asst_dealer"))
        self.assertEqual(response.status_code, 200)


class TestDealersOrdering(DealerTestCase):
    def setup_add_attendee_to_assistant(self, assistant_id):
        self.assertIsNone(self.assistant.attendee)
        session = self.client.session
        session["assistant_id"] = assistant_id
        session.save()
        ordering.add_attendee_to_assistant(self.client, self.attendee)
        self.assistant.refresh_from_db()

    def test_add_attendee_to_assistant(self):
        self.setup_add_attendee_to_assistant(self.assistant.pk)
        self.assertEqual(self.assistant.attendee, self.attendee)

    def test_add_attendee_to_assistant_does_not_exist(self):
        self.setup_add_attendee_to_assistant(0)
        self.assertIsNone(self.assistant.attendee)
