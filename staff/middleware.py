from django.shortcuts import redirect


class StaffLoginRedirectMiddleware:
    """
    Middleware to redirect staff members away from admin to their staff profile.
    This runs after login and checks if a staff member is trying to access admin.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user just logged in and is being redirected to admin
        if (
            request.user.is_authenticated
            and hasattr(request.user, "staff_profile")
            and request.user.staff_profile
            and request.path.startswith("/admin/")
            and not request.user.is_superuser
        ):
            # Redirect staff to their portal instead
            return redirect("staff:portal")

        response = self.get_response(request)
        return response
