import datetime

from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from registration.models import *
from registration.templatetags import site as site_tags
from registration.tests.common import *


class Index(TestCase):
    def setUp(self):
        self.client = Client()

    # unit tests skip methods that start with uppercase letters
    def TestIndex(self):
        response = self.client.get(reverse("registration:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the registration system")

    def TestIndexClosedUpcoming(self, home_link):
        response = self.client.get(reverse("registration:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not yet open")
        self.assertContains(response, f'<a href="{home_link}">Back to Main Page</a>')

    def TestIndexClosedEnded(self, home_link):
        response = self.client.get(reverse("registration:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has ended")
        self.assertContains(response, f'<a href="{home_link}">Back to Main Page</a>')

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
        self.event.attendeeRegStart = now + one_day
        self.event.attendeeRegEnd = now + ten_days
        self.event.save()
        self.TestIndexClosedUpcoming(home_link="/registration/")

        self.event.websiteUrl = "https://example.com"
        self.event.save()

        self.TestIndexClosedUpcoming(home_link="https://example.com")

        self.event.websiteUrl = ""
        self.event.save()

        self.event.attendeeRegStart = now - ten_days
        self.event.attendeeRegEnd = now - one_day
        self.event.save()
        self.TestIndexClosedEnded(home_link="/registration/")

        self.event.websiteUrl = "https://example.com"
        self.event.save()

        self.TestIndexClosedEnded(home_link="https://example.com")

        self.event.websiteUrl = ""
        self.event.save()


class TestTemplateTags(TestCase):
    def setUp(self):
        self.event = Event(
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
        self.event.save()
        self.client = Client()

    def test_bootstrap_message(self):
        self.assertEqual(site_tags.bootstrap_message("debug"), "alert-info")
        self.assertEqual(site_tags.bootstrap_message("not-a-real-category"), "")

    def test_current_domain(self):
        self.assertEqual(site_tags.current_domain(), "example.com")

    def test_current_site_name(self):
        self.assertEqual(site_tags.current_site_name(), "example.com")

    # def test_js_date(self):
    #     date = datetime.date(2020, 10, 5)
    #     self.assertEqual(site_tags.js_date(date), "Date(2020, 9, 5)")


class RobotsTest(TestCase):
    def test_get(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")
