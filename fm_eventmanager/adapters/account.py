from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import get_next_redirect_url
from django.urls import reverse


class RegistrationAccountAdapter(DefaultAccountAdapter):
    def __init__(self, request=None):
        print("DEBUG: RegistrationAccountAdapter initialized")
        super().__init__(request)
    
    def is_open_for_signup(self, _request):
        return False
    
    def get_login_redirect_url(self, request):
        """
        Determine where to redirect after login based on staff profile.
        Staff members ALWAYS go to their profile, ignoring 'next' parameter.
        Priority:
        1. If user has staff profile with department landing page, use it
        2. If user has staff profile, go to staff profile page
        3. Otherwise, use default behavior (respects 'next' parameter)
        """
        user = request.user
        
        print(f"DEBUG: get_login_redirect_url called for user: {user.username}")
        print(f"DEBUG: has staff_profile attr: {hasattr(user, 'staff_profile')}")
        
        # For staff members, ignore the 'next' parameter and send to profile
        if hasattr(user, "staff_profile") and user.staff_profile:
            staff = user.staff_profile
            print(f"DEBUG: Staff profile found: {staff}")
            
            # First check if department has a custom landing page
            if staff.department and staff.department.default_landing_page:
                landing_page = staff.department.default_landing_page
                print(f"DEBUG: Using department landing page: {landing_page}")
                if landing_page.startswith("/"):
                    return landing_page
                else:
                    try:
                        return reverse(landing_page)
                    except Exception:
                        return landing_page
            
            # Go to staff profile page
            print(f"DEBUG: Redirecting to staff:profile")
            return reverse("staff:profile")

        # Fall back to default behavior (respects next, uses LOGIN_REDIRECT_URL)
        print(f"DEBUG: Using default redirect behavior")
        return super().get_login_redirect_url(request)
    
    def get_email_confirmation_redirect_url(self, request):
        """
        Override to also handle staff redirects after email confirmation.
        """
        user = request.user
        if hasattr(user, "staff_profile") and user.staff_profile:
            return reverse("staff:profile")
        return super().get_email_confirmation_redirect_url(request)

