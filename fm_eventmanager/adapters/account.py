from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class RegistrationAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, _request):
        return False

    def get_login_redirect_url(self, request):
        """
        Determine where to redirect after login based on staff profile.
        Staff members ALWAYS go to their profile (handled by middleware for admin URLs).
        Priority:
        1. If user has staff profile with department landing page, use it
        2. If user has staff profile, go to staff profile page
        3. Otherwise, use default behavior (respects 'next' parameter)
        """
        user = request.user

        # For staff members, send to profile (or custom department landing page)
        if hasattr(user, "staff_profile") and user.staff_profile:
            staff = user.staff_profile

            # First check if department has a custom landing page
            if staff.department and staff.department.default_landing_page:
                landing_page = staff.department.default_landing_page
                if landing_page.startswith("/"):
                    return landing_page
                else:
                    try:
                        return reverse(landing_page)
                    except Exception:
                        return landing_page

            # Go to staff profile page
            return reverse("staff:profile")

        # Fall back to default behavior (respects next, uses LOGIN_REDIRECT_URL)
        return super().get_login_redirect_url(request)

    def get_email_confirmation_redirect_url(self, request):
        """
        Override to also handle staff redirects after email confirmation.
        """
        user = request.user
        if hasattr(user, "staff_profile") and user.staff_profile:
            return reverse("staff:profile")
        return super().get_email_confirmation_redirect_url(request)
