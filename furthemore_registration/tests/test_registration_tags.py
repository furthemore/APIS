from unittest import TestCase

from registration.models import Event, Venue
from registration.templatetags import registration_tags
from registration.tests.common import DEFAULT_EVENT_ARGS


class TestTags(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(country="Pastafaria")
        self.venue.save()
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()

    def test_venue_country_empty(self):
        result = registration_tags.venue_country(self.event)
        self.assertEqual(result, "")

    def test_venue_country_value(self):
        self.event.venue = self.venue
        result = registration_tags.venue_country(self.event)
        self.assertEqual(result, self.venue.country)

    def test_get_value(self):
        d = {"foo": "bar"}
        result = registration_tags.get_value(d, "foo")
        self.assertEqual(result, "bar")
