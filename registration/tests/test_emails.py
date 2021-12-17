from unittest import TestCase

from django.core import mail
from django.test import TestCase
from mock import patch

from registration import emails
from registration.models import (
    Attendee,
    Badge,
    Dealer,
    DealerAsst,
    Event,
    Order,
    Staff,
    TempToken,
)
from registration.tests.common import DEFAULT_EVENT_ARGS


class TestSendEmail(TestCase):
    def send_email(self):
        emails.send_email(
            "no-reply@example.com",
            ["someone@mailinator.org"],
            "Test email subject",
            "This is a test",
            "<p>This is a test</p>",
        )

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, "Test email subject")


class EmailTestCase(TestCase):
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
        self.badge = Badge(
            attendee=self.attendee, event=self.event, badgeName="DisStaff"
        )
        self.badge.save()
        self.token = TempToken(email=self.attendee.email, validUntil="2048-12-12")
        self.order = Order(
            total=60, reference="HUGBUG", billingEmail=self.attendee.email
        )
        self.order.save()


class TestStaffEmails(EmailTestCase):
    def setUp(self):
        super().setUp()
        self.staff = Staff(attendee=self.attendee, event=self.event)
        self.staff.save()

    @patch("registration.emails.send_email")
    def test_send_new_staff_email(self, mock_send_email):
        emails.send_new_staff_email(self.token)
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertIn(self.token.token, plain_text)
        self.assertIn(self.token.token, html_text)
        self.assertEqual(recipients, [self.attendee.email])

    @patch("registration.emails.send_email")
    def test_send_staff_promotion_email(self, mock_send_email):
        emails.send_staff_promotion_email(self.staff)
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertIn(self.staff.registrationToken, plain_text)
        self.assertIn(self.staff.registrationToken, html_text)
        self.assertEqual(recipients, [self.attendee.email])

    @patch("registration.emails.send_email")
    def test_send_staff_registration_email(self, mock_send_email):
        emails.send_staff_registration_email(self.order.pk)
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertIn(self.order.reference, plain_text)
        self.assertIn(self.order.reference, html_text)
        self.assertEqual(recipients, [self.attendee.email])


class TestDealerEmails(EmailTestCase):
    def setUp(self):
        super().setUp()
        self.dealer = Dealer(
            attendee=self.attendee,
            businessName="Rechner's Unit Testing Emporium",
            website="furthemore.org",
            description="Just some unit testing",
            license="To kill",
            event=self.event,
        )
        self.dealer.save()
        self.assistant = DealerAsst(
            dealer=self.dealer,
            name="Taschenrechner",
            email="someone@mailinator.com",
            license="Gratuitous",
            event=self.event,
        )
        self.assistant.save()

    @patch("registration.emails.send_email")
    def test_send_dealer_application_email(self, mock_send_email):
        emails.send_dealer_application_email(self.dealer.pk)
        self.assertEqual(mock_send_email.call_count, 2)
        first_call, second_call = mock_send_email.call_args_list
        recipients = first_call[0][1]
        self.assertEqual(recipients, [self.attendee.email])
        recipients = second_call[0][1]
        self.assertEqual(recipients, [self.event.dealerEmail])

    @patch("registration.emails.send_email")
    def test_send_dealer_approval_email(self, mock_send_email):
        emails.send_dealer_approval_email([self.dealer])
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertEqual(recipients, [self.attendee.email])
        self.assertIn(self.dealer.registrationToken, plain_text)
        self.assertIn(self.dealer.registrationToken, html_text)

    @patch("registration.emails.send_email")
    def test_send_dealer_assistant_form_email(self, mock_send_email):
        emails.send_dealer_assistant_form_email(self.dealer)
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertEqual(recipients, [self.attendee.email])
        self.assertIn(self.dealer.registrationToken, plain_text)
        self.assertIn(self.dealer.registrationToken, html_text)

    @patch("registration.emails.send_email")
    def test_send_dealer_assistant_email(self, mock_send_email):
        emails.send_dealer_assistant_email(self.dealer.pk)
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        self.assertEqual(recipients, [self.attendee.email])

    @patch("registration.emails.send_email")
    def test_send_dealer_payment_email(self, mock_send_email):
        # TODO: test the payment receipt formatting better
        emails.send_dealer_payment_email(self.dealer, self.order)
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertEqual(recipients, [self.attendee.email])
        self.assertIn(self.order.reference, plain_text)
        self.assertIn(self.order.reference, html_text)

    @patch("registration.emails.send_email")
    def test_send_dealer_assistant_registration_invite(self, mock_send_email):
        emails.send_dealer_assistant_registration_invite(self.assistant)
        mock_send_email.assert_called_once()
        recipients = mock_send_email.call_args[0][1]
        plain_text = mock_send_email.call_args[0][3]
        html_text = mock_send_email.call_args[0][4]
        self.assertEqual(recipients, [self.assistant.email])
        self.assertIn(self.assistant.registrationToken, plain_text)
        self.assertIn(self.assistant.registrationToken, html_text)
