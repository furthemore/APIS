from django.test import TestCase
from decimal import Decimal

from registration.models import Charity, Venue
from registration.tests.common import DEFAULT_VENUE_ARGS


class TestCharity(TestCase):
    def setUp(self):
        self.charity = Charity(name="Reconstructing the Past", donations=5.00)
        self.charity.save()
        self.charity.refresh_from_db()

    def test_charity_fields(self):
        self.assertIsInstance(self.charity.name, str)
        self.assertIsInstance(self.charity.url, str)
        self.assertIsInstance(self.charity.donations, Decimal)
        self.assertEquals(str(self.charity), self.charity.name)


class TestVenue(TestCase):
    def setUp(self):
        self.venue = Venue(**DEFAULT_VENUE_ARGS)
        self.venue.save()

    def test_venue_fields(self):
        self.assertIsInstance(self.venue.name, str)
        self.assertIsInstance(self.venue.address, str)
        self.assertIsInstance(self.venue.city, str)
        self.assertIsInstance(self.venue.state, str)
        self.assertIsInstance(self.venue.country, str)
        self.assertEquals(str(self.venue), self.venue.name)
