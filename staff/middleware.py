from django.shortcuts import redirect


class StaffLoginRedirectMiddleware:
    """
    Redirect users who have a staff profile but lack admin access (is_staff=False)
    from /admin/ to the staff portal. Users with is_staff=True are not redirected.
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
            and not request.user.is_staff
        ):
            # Users with a staff profile but no admin access (is_staff=False)
            # go to the portal. Users with is_staff keep access to the admin
            # and are limited by their own permissions.
            return redirect("staff:portal")

        response = self.get_response(request)
        return response
