from decimal import Decimal

from django.test import TestCase

from registration.models import (
    Attendee,
    Charity,
    HoldType,
    Venue,
    get_hold_type,
)
from registration.tests.common import DEFAULT_VENUE_ARGS, TEST_ATTENDEE_ARGS


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


class TestAttendee(TestCase):
    def setUp(self):
        self.attendee = Attendee(*TEST_ATTENDEE_ARGS)

    def test_preferredName(self):
        preferredName = "Someone else"
        self.attendee.preferredName = preferredName
        self.assertEqual(self.attendee.getFirst(), preferredName)


class TestHoldType(TestCase):
    def setUp(self):
        self.existing_hold = HoldType(name="Existing Hold")
        self.existing_hold.save()
        self.existing_hold.refresh_from_db()

    def test_get_hold_type_existing_hold(self):
        hold = get_hold_type("Existing Hold")
        self.assertEqual(self.existing_hold, hold)

    def test_get_hold_type_new(self):
        hold = get_hold_type("New Hold")
        self.assertNotEqual(self.existing_hold, hold)
