from django.test import TestCase
from mock import patch

from registration.models import Event, Badge, Attendee, TempToken
from registration import emails
from registration.tests.common import DEFAULT_EVENT_ARGS


class TestStaffEmails(TestCase):
    def setUp(self):
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()

        self.attendee = Attendee(
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
        self.attendee.save()
        self.badge = Badge(attendee=self.attendee, event=self.event, badgeName="DisStaff")
        self.badge.save()
        self.token = TempToken(email=self.attendee.email, validUntil="2048-12-12")

    @patch("registration.emails.sendEmail")
    def test_send_new_staff_email(self, mock_sendEmail):
        emails.send_new_staff_email(self.token)
        mock_sendEmail.assert_called_once()
