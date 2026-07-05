from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class RegistrationAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, _request):
        return False

    def get_login_redirect_url(self, request):
        """
        Determine where to redirect after login based on staff department.
        Priority:
        1. If user has staff profile with department that has a landing page, use it
        2. If user is admin/superuser, go to admin
        3. Otherwise, use default LOGIN_REDIRECT_URL
        """
        user = request.user

        # Check if user has a linked staff profile with department
        if hasattr(user, "staff_profile") and user.staff_profile:
            staff = user.staff_profile
            if staff.department and staff.department.default_landing_page:
                landing_page = staff.department.default_landing_page
                # Handle both URL paths and named URLs
                if landing_page.startswith("/"):
                    return landing_page
                else:
                    try:
                        return reverse(landing_page)
                    except Exception:
                        # If reverse fails, treat as path
                        return landing_page

        # Admins go to admin by default
        if user.is_staff or user.is_superuser:
            return reverse("admin:index")

        # Fall back to default behavior (uses LOGIN_REDIRECT_URL from settings)
        return super().get_login_redirect_url(request)

