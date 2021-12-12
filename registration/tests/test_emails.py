from django.test import TestCase
from mock import patch

from registration.models import Event, Badge, Staff, Attendee, TempToken, Order
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
        self.staff = Staff(attendee=self.attendee, event=self.event)
        self.staff.save()
        self.order = Order(
            total=60,
            reference="HUGBUG",
            billingEmail=self.attendee.email
        )
        self.order.save()

    @patch("registration.emails.sendEmail")
    def test_send_new_staff_email(self, mock_sendEmail):
        emails.send_new_staff_email(self.token)
        mock_sendEmail.assert_called_once()
        recipients = mock_sendEmail.call_args[0][1]
        plainText = mock_sendEmail.call_args[0][3]
        htmlText = mock_sendEmail.call_args[0][4]
        self.assertIn(self.token.token, plainText)
        self.assertIn(self.token.token, htmlText)
        self.assertEqual(recipients, [self.attendee.email])

    @patch("registration.emails.sendEmail")
    def test_send_staff_promotion_email(self, mock_sendEmail):
        emails.send_staff_promotion_email(self.staff)
        mock_sendEmail.assert_called_once()
        recipients = mock_sendEmail.call_args[0][1]
        plainText = mock_sendEmail.call_args[0][3]
        htmlText = mock_sendEmail.call_args[0][4]
        self.assertIn(self.staff.registrationToken, plainText)
        self.assertIn(self.staff.registrationToken, htmlText)
        self.assertEqual(recipients, [self.attendee.email])

    @patch("registration.emails.sendEmail")
    def test_sendStaffRegistrationEmail(self, mock_sendEmail):
        emails.sendStaffRegistrationEmail(self.order.pk)
        mock_sendEmail.assert_called_once()
        recipients = mock_sendEmail.call_args[0][1]
        plainText = mock_sendEmail.call_args[0][3]
        htmlText = mock_sendEmail.call_args[0][4]
        self.assertIn(self.order.reference, plainText)
        self.assertIn(self.order.reference, htmlText)
        self.assertEqual(recipients, [self.attendee.email])
