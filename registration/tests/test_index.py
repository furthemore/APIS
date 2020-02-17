from django.test import Client, TestCase
from django.urls import reverse

from registration.models import *
from registration.tests.common import *


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
