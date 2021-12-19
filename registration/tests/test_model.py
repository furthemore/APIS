from django.test import TestCase

from registration.models import Venue
from registration.tests.common import DEFAULT_VENUE_ARGS


class TestVenue(TestCase):
    def setUp(self):
        self.venue = Venue(**DEFAULT_VENUE_ARGS)
        self.save()

    def test_venue_fields(self):
        self.assert
