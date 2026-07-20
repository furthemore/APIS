"""
Tests for the staff app
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from registration.models import Event, ShirtSizes, Badge, PriceLevel
from staff.models import (
    Department,
    Staff,
    StaffPosition,
    StaffPosting,
    StaffApplicant,
    StaffInvite,
    StaffEventRegistration,
)


def create_test_event(name="Test Con 2027", days_ahead=30):
    """Helper to create a test event with all required fields"""
    now = timezone.now()
    return Event.objects.create(
        name=name,
        default=True,
        eventStart=(now + timedelta(days=days_ahead)).date(),
        eventEnd=(now + timedelta(days=days_ahead + 2)).date(),
        staffRegStart=now - timedelta(days=10),
        staffRegEnd=now + timedelta(days=20),
        attendeeRegStart=now - timedelta(days=10),
        attendeeRegEnd=now + timedelta(days=20),
        dealerRegStart=now - timedelta(days=10),
        dealerRegEnd=now + timedelta(days=20),
        onsiteRegStart=now + timedelta(days=days_ahead),
        onsiteRegEnd=now + timedelta(days=days_ahead + 2)
    )



class DepartmentModelTest(TestCase):
    """Tests for Department model"""

    def setUp(self):
        self.dept = Department.objects.create(
            name="Registration",
            volunteerListOk=True
        )
        self.sub_dept = Department.objects.create(
            name="Check-in",
            parent_department=self.dept,
            volunteerListOk=False
        )

    def test_department_creation(self):
        """Test basic department creation"""
        self.assertEqual(self.dept.name, "Registration")
        self.assertTrue(self.dept.volunteerListOk)
        self.assertIsNone(self.dept.parent_department)

    def test_department_hierarchy(self):
        """Test parent-child department relationship"""
        self.assertEqual(self.sub_dept.parent_department, self.dept)
        self.assertIn(self.sub_dept, self.dept.sub_departments.all())

    def test_department_str(self):
        """Test department string representation"""
        self.assertEqual(str(self.dept), "Registration")
        self.assertEqual(str(self.sub_dept), "Registration > Check-in")


class StaffModelTest(TestCase):
    """Tests for Staff model"""

    def setUp(self):
        self.user = User.objects.create_user(username="teststaff", email="test@test.com")
        self.dept = Department.objects.create(name="Tech")
        self.staff = Staff.objects.create(
            user=self.user,
            department=self.dept,
            legal_first_name="John",
            legal_last_name="Doe",
            preferred_first_name="Johnny",
            email="john@example.com",
            birthdate="1990-01-01",
            title="Tech Lead"
        )

    def test_staff_creation(self):
        """Test staff profile creation"""
        self.assertEqual(self.staff.legal_first_name, "John")
        self.assertEqual(self.staff.department, self.dept)
        self.assertIsNotNone(self.staff.registration_token)
        self.assertFalse(self.staff.onboarding_complete)

    def test_staff_registration_token_auto_generated(self):
        """Test that registration token is automatically generated"""
        new_staff = Staff.objects.create(
            legal_first_name="Jane",
            legal_last_name="Smith",
            email="jane@example.com",
            birthdate="1992-05-15",
            title="Staff"
        )
        self.assertIsNotNone(new_staff.registration_token)
        self.assertTrue(len(new_staff.registration_token) > 0)

    def test_staff_first_name_preferred(self):
        """Test first_name() method returns preferred name when available"""
        self.assertEqual(self.staff.first_name(), "Johnny")
        
        # Test fallback to legal name
        staff_no_pref = Staff.objects.create(
            legal_first_name="Bob",
            legal_last_name="Smith",
            email="bob@example.com",
            birthdate="1985-03-10",
            title="Staff"
        )
        self.assertEqual(staff_no_pref.first_name(), "Bob")

    def test_staff_user_relationship(self):
        """Test OneToOne relationship with User"""
        self.assertEqual(self.user.staff_profile, self.staff)


class StaffPositionTest(TestCase):
    """Tests for StaffPosition model"""

    def setUp(self):
        self.dept = Department.objects.create(name="Operations")
        self.position = StaffPosition.objects.create(
            title="Event Coordinator",
            position_type=StaffPosition.HELD_POSITION,
            department=self.dept,
            description="Coordinates event operations"
        )

    def test_position_creation(self):
        """Test staff position creation"""
        self.assertEqual(self.position.title, "Event Coordinator")
        self.assertEqual(self.position.position_type, StaffPosition.HELD_POSITION)
        self.assertEqual(self.position.department, self.dept)

    def test_position_types(self):
        """Test different position types"""
        pool = StaffPosition.objects.create(
            title="General Staff",
            position_type=StaffPosition.STAFF_POOL,
            department=self.dept
        )
        volunteer = StaffPosition.objects.create(
            title="Volunteer",
            position_type=StaffPosition.VOLUNTEER_POOL,
            department=self.dept
        )
        
        self.assertEqual(pool.position_type, StaffPosition.STAFF_POOL)
        self.assertEqual(volunteer.position_type, StaffPosition.VOLUNTEER_POOL)


class StaffPostingTest(TestCase):
    """Tests for StaffPosting model"""

    def setUp(self):
        self.dept = Department.objects.create(name="Tech")
        self.position = StaffPosition.objects.create(
            title="Developer",
            position_type=StaffPosition.STAFF_POOL,
            department=self.dept
        )
        self.event = create_test_event()
        self.posting = StaffPosting.objects.create(
            position=self.position,
            event=self.event,
            slots=3,
            is_open=True
        )

    def test_posting_creation(self):
        """Test staff posting creation"""
        self.assertEqual(self.posting.position, self.position)
        self.assertEqual(self.posting.event, self.event)
        self.assertEqual(self.posting.slots, 3)
        self.assertTrue(self.posting.is_open)

    def test_posting_without_event(self):
        """Test ongoing posting without specific event"""
        ongoing = StaffPosting.objects.create(
            position=self.position,
            event=None,
            slots=5,
            is_open=True
        )
        self.assertIsNone(ongoing.event)
        self.assertEqual(str(ongoing), "Developer (Ongoing)")


class StaffInviteTest(TestCase):
    """Tests for StaffInvite model"""

    def setUp(self):
        self.invite = StaffInvite.objects.create(
            email="newstaff@example.com",
            valid_until=timezone.now() + timedelta(days=7),
            ignore_time_window=False
        )

    def test_invite_creation(self):
        """Test staff invite creation"""
        self.assertEqual(self.invite.email, "newstaff@example.com")
        self.assertFalse(self.invite.used)
        self.assertFalse(self.invite.sent)
        self.assertIsNotNone(self.invite.token)

    def test_invite_token_auto_generated(self):
        """Test that invite token is automatically generated"""
        self.assertTrue(len(self.invite.token) > 0)


class StaffEventRegistrationTest(TestCase):
    """Tests for StaffEventRegistration model"""

    def setUp(self):
        self.staff = Staff.objects.create(
            legal_first_name="Test",
            legal_last_name="Staff",
            email="teststaff@example.com",
            birthdate="1990-01-01",
            title="Staff"
        )
        self.event = create_test_event()
        self.shirt = ShirtSizes.objects.create(name="Medium")
        self.registration = StaffEventRegistration.objects.create(
            staff=self.staff,
            event=self.event,
            shirt_size=self.shirt,
            contact_name="Emergency Contact",
            contact_phone="555-1234"
        )

    def test_event_registration_creation(self):
        """Test staff event registration creation"""
        self.assertEqual(self.registration.staff, self.staff)
        self.assertEqual(self.registration.event, self.event)
        self.assertEqual(self.registration.shirt_size, self.shirt)
        self.assertFalse(self.registration.checked_in)

    def test_unique_staff_event_registration(self):
        """Test that staff can only register once per event"""
        with self.assertRaises(Exception):
            StaffEventRegistration.objects.create(
                staff=self.staff,
                event=self.event,
                shirt_size=self.shirt
            )


class StaffViewsTest(TestCase):
    """Tests for staff views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            email="staff@example.com"
        )
        self.dept = Department.objects.create(name="Operations")
        self.staff = Staff.objects.create(
            user=self.user,
            department=self.dept,
            legal_first_name="Staff",
            legal_last_name="Member",
            email="staff@example.com",
            birthdate="1988-06-15",
            title="Operations Lead"
        )
        self.event = create_test_event()

    def test_index_redirect_authenticated(self):
        """Test index redirects authenticated staff to portal"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse('staff:index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('staff:portal')))

    def test_index_redirect_unauthenticated(self):
        """Test index redirects unauthenticated users to openings"""
        response = self.client.get(reverse('staff:index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('staff:openings')))

    def test_portal_requires_login(self):
        """Test portal requires authentication"""
        response = self.client.get(reverse('staff:portal'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('login' in response.url)

    def test_portal_requires_staff_profile(self):
        """Test portal requires staff profile"""
        user_no_staff = User.objects.create_user(
            username="nostaff",
            password="testpass123"
        )
        self.client.login(username="nostaff", password="testpass123")
        response = self.client.get(reverse('staff:portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "do not have a staff profile")

    def test_portal_shows_for_staff(self):
        """Test portal displays for staff with profile"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse('staff:portal'))
        self.assertEqual(response.status_code, 200)

    def test_openings_page(self):
        """Test openings page displays open postings"""
        position = StaffPosition.objects.create(
            title="Test Position",
            position_type=StaffPosition.STAFF_POOL,
            department=self.dept
        )
        posting = StaffPosting.objects.create(
            position=position,
            event=self.event,
            slots=2,
            is_open=True
        )
        
        response = self.client.get(reverse('staff:openings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Position")


class StaffRegistrationTest(TestCase):
    """Tests for staff registration flow"""

    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Tech")
        self.staff = Staff.objects.create(
            legal_first_name="Test",
            legal_last_name="Staff",
            email="test@example.com",
            birthdate="1990-01-01",
            title="Developer",
            department=self.dept,
            street_address_1="123 Main St",
            city="Test City",
            state="CA",
            country="USA",
            postal_code="12345"
        )
        self.event = create_test_event()
        self.shirt = ShirtSizes.objects.create(name="Large")
        self.price_level = PriceLevel.objects.create(
            name="Staff",
            basePrice=0,
            startDate=timezone.now() - timedelta(days=30),
            endDate=timezone.now() + timedelta(days=60),
            available_to_staff=True
        )

    def test_register_with_staff_token(self):
        """Test registration using staff.registration_token"""
        response = self.client.get(
            reverse('staff:register', kwargs={'token': self.staff.registration_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Staff")

    def test_register_with_invite_token(self):
        """Test registration using StaffInvite token"""
        invite = StaffInvite.objects.create(
            email=self.staff.email,
            valid_until=timezone.now() + timedelta(days=7)
        )
        
        response = self.client.get(
            reverse('staff:register', kwargs={'token': invite.token})
        )
        self.assertEqual(response.status_code, 200)

    def test_register_invalid_token(self):
        """Test registration with invalid token"""
        response = self.client.get(
            reverse('staff:register', kwargs={'token': 'INVALIDTOKEN123'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid registration token")

    def test_register_already_registered(self):
        """Test registration when already registered"""
        # Create existing registration
        StaffEventRegistration.objects.create(
            staff=self.staff,
            event=self.event,
            shirt_size=self.shirt
        )
        
        response = self.client.get(
            reverse('staff:register', kwargs={'token': self.staff.registration_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered")

    def test_register_post_creates_registration(self):
        """Test POST to register creates StaffEventRegistration and Badge"""
        data = {
            'street_address_1': '456 New St',
            'city': 'New City',
            'state': 'NY',
            'country': 'USA',
            'postal_code': '54321',
            'shirt_size': self.shirt.id,
            'contact_name': 'Emergency',
            'contact_phone': '555-0000',
        }
        
        response = self.client.post(
            reverse('staff:register', kwargs={'token': self.staff.registration_token}),
            data
        )
        
        # Should redirect to complete page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('staff:register_complete')))
        
        # Check registration was created
        registration = StaffEventRegistration.objects.get(staff=self.staff, event=self.event)
        self.assertEqual(registration.shirt_size, self.shirt)
        
        # Check badge was created
        badge = Badge.objects.get(staff=self.staff, event=self.event)
        self.assertIsNotNone(badge)
        self.assertEqual(badge.badgeName, self.staff.first_name())

    def test_register_rotates_token(self):
        """Test that registration rotates staff token"""
        old_token = self.staff.registration_token
        
        data = {
            'street_address_1': '456 New St',
            'city': 'New City',
            'state': 'NY',
            'country': 'USA',
            'postal_code': '54321',
            'shirt_size': self.shirt.id,
            'contact_name': 'Emergency',
            'contact_phone': '555-0000',
        }
        
        self.client.post(
            reverse('staff:register', kwargs={'token': old_token}),
            data
        )
        
        # Refresh from database
        self.staff.refresh_from_db()
        self.assertNotEqual(self.staff.registration_token, old_token)


class StaffEmailTest(TestCase):
    """Tests for staff email functions"""

    def setUp(self):
        self.event = create_test_event()
        self.invite = StaffInvite.objects.create(
            email="newstaff@example.com",
            valid_until=timezone.now() + timedelta(days=7)
        )

    @patch('staff.emails.send_email')
    def test_send_staff_invitation_email(self, mock_send_email):
        """Test sending staff invitation email"""
        from staff.emails import send_staff_invitation_email
        
        send_staff_invitation_email(self.invite)
        
        mock_send_email.assert_called_once()
        args = mock_send_email.call_args
        self.assertIn(self.invite.email, args[0][1])
        self.assertIn("Welcome", args[0][2])

    @patch('staff.emails.send_email')
    def test_send_staff_registration_confirmation(self, mock_send_email):
        """Test sending registration confirmation email"""
        from staff.emails import send_staff_registration_confirmation
        
        staff = Staff.objects.create(
            legal_first_name="Test",
            legal_last_name="Staff",
            email="test@example.com",
            birthdate="1990-01-01",
            title="Staff"
        )
        registration = StaffEventRegistration.objects.create(
            staff=staff,
            event=self.event
        )
        
        send_staff_registration_confirmation(staff, registration, "TEST123")
        
        mock_send_email.assert_called_once()
        args = mock_send_email.call_args
        self.assertIn(staff.email, args[0][1])
        self.assertIn("Confirmed", args[0][2])


class StaffMiddlewareTest(TestCase):
    """Tests for StaffLoginRedirectMiddleware"""

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@example.com"
        )
        self.staff_user = User.objects.create_user(
            username="staffmember",
            password="staff123",
            email="staff@example.com",
            is_staff=True
        )
        self.staff_profile = Staff.objects.create(
            user=self.staff_user,
            legal_first_name="Staff",
            legal_last_name="Member",
            email="staff@example.com",
            birthdate="1990-01-01",
            title="Staff"
        )

    def test_staff_redirected_from_admin(self):
        """Test staff with profile redirected away from admin"""
        self.client.login(username="staffmember", password="staff123")
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('staff:portal')))

    def test_superuser_can_access_admin(self):
        """Test superuser can still access admin"""
        self.client.login(username="admin", password="admin123")
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)


class BadgeStaffLinkTest(TestCase):
    """Tests for Badge-Staff relationship"""

    def setUp(self):
        self.event = create_test_event()
        self.staff = Staff.objects.create(
            legal_first_name="Badge",
            legal_last_name="Test",
            email="badge@example.com",
            birthdate="1990-01-01",
            title="Staff",
            fandom_name="BadgeName"
        )

    def test_badge_linked_to_staff(self):
        """Test badge can be linked to staff profile"""
        badge = Badge.objects.create(
            staff=self.staff,
            event=self.event,
            badgeName=self.staff.fandom_name
        )
        
        self.assertEqual(badge.staff, self.staff)
        self.assertIsNone(badge.attendee)

    def test_badge_status_for_staff(self):
        """Test badge.abandoned property returns Staff for staff badges"""
        badge = Badge.objects.create(
            staff=self.staff,
            event=self.event,
            badgeName="Test Badge"
        )
        
        self.assertEqual(badge.abandoned, Badge.STAFF)
