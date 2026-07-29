from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from registration.models import (
    Badge,
    Event,
    OrderItem,
    PriceLevel,
    get_registration_token,
)
from staff.forms import StaffApplicationForm, StaffRegistrationForm
from staff.models import (
    Department,
    Staff,
    StaffApplicant,
    StaffEventRegistration,
    StaffInvite,
    StaffPosting,
)


def index(request):
    """
    Redirect to appropriate page:
    - If user is authenticated and has a staff profile, redirect to portal
    - Otherwise, redirect to openings (public view)
    """
    if request.user.is_authenticated and hasattr(request.user, "staff_profile"):
        return redirect("staff:portal")
    return redirect("staff:openings")


@login_required
def profile(request):
    """
    Staff profile view - shows different content based on role:
    - Department heads/assistant heads: Dashboard with department stats
    - Regular staff: Personal profile summary
    """
    # Check if user has a staff profile
    if not hasattr(request.user, "staff_profile"):
        return render(
            request,
            "staff/profile_no_access.html",
            {
                "message": "You do not have a staff profile. Please contact an administrator."
            },
        )

    staff_profile = request.user.staff_profile

    # Get current/default event
    try:
        current_event = Event.objects.get(default=True)
    except Event.DoesNotExist:
        current_event = None

    # Get registration token from staff profile
    registration_token = staff_profile.registration_token if current_event else None

    # Check if user is a department head or assistant head
    is_department_leader = (
        Department.objects.filter(heads=staff_profile).exists()
        or Department.objects.filter(assistant_heads=staff_profile).exists()
    )

    if is_department_leader:
        # Get departments they lead
        led_departments = Department.objects.filter(
            models.Q(heads=staff_profile) | models.Q(assistant_heads=staff_profile)
        ).distinct()

        # Build stats for each department
        department_stats = []
        for dept in led_departments:
            # Get direct staff count
            direct_staff_count = Staff.objects.filter(department=dept).count()

            # Get all staff including sub-departments
            all_staff = dept.get_all_staff()
            total_staff = all_staff.count()

            # Count how many are registered for current event
            registered_count = 0
            if current_event:
                registered_count = StaffEventRegistration.objects.filter(
                    staff__department=dept, event=current_event
                ).count()

            # Get staff list with their registration status (direct members only)
            staff_list = []
            for staff_member in Staff.objects.filter(department=dept).select_related(
                "user"
            ):
                # Check if they're registered for current event
                is_registered = False
                event_registration = None
                if current_event:
                    event_registration = StaffEventRegistration.objects.filter(
                        staff=staff_member, event=current_event
                    ).first()
                    is_registered = event_registration is not None

                staff_list.append(
                    {
                        "staff": staff_member,
                        "is_registered": is_registered,
                        "checked_in": (
                            event_registration.checked_in
                            if event_registration
                            else False
                        ),
                    }
                )

            # Get sub-departments with their stats
            sub_dept_stats = []
            for sub_dept in dept.sub_departments.all():
                sub_staff_count = Staff.objects.filter(department=sub_dept).count()
                sub_registered_count = 0
                if current_event:
                    sub_registered_count = StaffEventRegistration.objects.filter(
                        staff__department=sub_dept, event=current_event
                    ).count()

                # Get staff list for sub-department
                sub_staff_list = []
                for staff_member in Staff.objects.filter(
                    department=sub_dept
                ).select_related("user"):
                    # Check if they're registered for current event
                    is_registered = False
                    event_registration = None
                    if current_event:
                        event_registration = StaffEventRegistration.objects.filter(
                            staff=staff_member, event=current_event
                        ).first()
                        is_registered = event_registration is not None

                    sub_staff_list.append(
                        {
                            "staff": staff_member,
                            "is_registered": is_registered,
                            "checked_in": (
                                event_registration.checked_in
                                if event_registration
                                else False
                            ),
                        }
                    )

                sub_dept_stats.append(
                    {
                        "department": sub_dept,
                        "staff_count": sub_staff_count,
                        "registered_count": sub_registered_count,
                        "staff_list": sub_staff_list,
                    }
                )

            department_stats.append(
                {
                    "department": dept,
                    "direct_staff_count": direct_staff_count,
                    "total_staff": total_staff,
                    "registered_count": registered_count,
                    "staff_list": staff_list,
                    "sub_departments": sub_dept_stats,
                }
            )

        # Check personal registration status for leader as well
        is_registered = False
        event_registration = None
        if current_event:
            event_registration = StaffEventRegistration.objects.filter(
                staff=staff_profile, event=current_event
            ).first()
            is_registered = event_registration is not None

        context = {
            "staff_profile": staff_profile,
            "is_department_leader": True,
            "current_event": current_event,
            "department_stats": department_stats,
            "registration_token": registration_token,
            "is_registered": is_registered,
            "registration_record": event_registration,
        }
        return render(request, "staff/profile_leader.html", context)

    else:
        # Regular staff member - show personal summary
        # Check if they're registered for current event
        is_registered = False
        event_registration = None
        if current_event:
            event_registration = StaffEventRegistration.objects.filter(
                staff=staff_profile, event=current_event
            ).first()
            is_registered = event_registration is not None

        context = {
            "staff_profile": staff_profile,
            "is_department_leader": False,
            "current_event": current_event,
            "is_registered": is_registered,
            "registration_record": event_registration,
            "registration_token": registration_token,
        }
        return render(request, "staff/profile_staff.html", context)


def openings(request):
    """List all open staff postings."""
    postings = (
        StaffPosting.objects.filter(is_open=True)
        .select_related("position", "position__department", "event")
        .order_by("position__position_type", "position__title")
    )

    context = {
        "postings": postings,
    }
    return render(request, "staff/openings.html", context)


def apply(request, posting_id):
    """Application form for a specific posting."""
    posting = get_object_or_404(
        StaffPosting.objects.select_related(
            "position", "position__department", "event"
        ),
        id=posting_id,
        is_open=True,
    )

    if request.method == "POST":
        form = StaffApplicationForm(request.POST)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.posting = posting
            applicant.registration_token = get_registration_token()
            applicant.save()
            return redirect("staff:application", applicant_id=applicant.id)
    else:
        form = StaffApplicationForm()

    context = {
        "posting": posting,
        "form": form,
    }
    return render(request, "staff/apply.html", context)


def application(request, applicant_id):
    """Confirmation page after submitting an application."""
    applicant = get_object_or_404(
        StaffApplicant.objects.select_related("posting", "posting__position"),
        id=applicant_id,
    )

    context = {
        "applicant": applicant,
    }
    return render(request, "staff/application.html", context)


def register(request, token):
    """
    Staff registration for current event using token.
    Supports two token types:
    1. Staff.registration_token for returning staff (rotates after use)
    2. StaffInvite.token for new staff not yet in system
    """
    # Get current event
    try:
        event = Event.objects.get(default=True)
    except Event.DoesNotExist:
        return render(
            request,
            "staff/register_error.html",
            {"error": "No active event found. Please contact staff coordinators."},
        )

    staff_profile = None
    is_invite_token = False
    invite = None

    # Try to find staff by their registration_token (returning staff)
    staff_profile = Staff.objects.filter(registration_token=token).first()

    # If not found, try StaffInvite token (new staff)
    if not staff_profile:
        try:
            invite = StaffInvite.objects.get(token=token)
            if invite.used:
                return render(
                    request,
                    "staff/register_error.html",
                    {"error": "This registration link has already been used."},
                )
            is_invite_token = True

            # Find staff profile by email from invite
            try:
                staff_profile = Staff.objects.get(email=invite.email)
            except Staff.DoesNotExist:
                return render(
                    request,
                    "staff/register_error.html",
                    {
                        "error": "No staff profile found for this email. Please contact staff coordinators."
                    },
                )
        except StaffInvite.DoesNotExist:
            return render(
                request,
                "staff/register_error.html",
                {"error": "Invalid registration token."},
            )

    # Check if already registered for this event
    existing_reg = StaffEventRegistration.objects.filter(
        staff=staff_profile, event=event
    ).first()
    if existing_reg:
        return render(
            request,
            "staff/register_error.html",
            {
                "error": "You are already registered for this event.",
                "is_info": True,
            },
        )

    if request.method == "POST":
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            # Create StaffEventRegistration
            event_reg = StaffEventRegistration(
                staff=staff_profile,
                event=event,
                registration_token=get_registration_token(),
                shirt_size=form.cleaned_data["shirt_size"],
                bluesky=form.cleaned_data["bluesky"],
                telegram=form.cleaned_data["telegram"],
                contact_name=form.cleaned_data["contact_name"],
                contact_phone=form.cleaned_data["contact_phone"],
                contact_relation=form.cleaned_data["contact_relation"],
                special_skills=form.cleaned_data["special_skills"],
                special_food=form.cleaned_data["special_food"],
                special_medical=form.cleaned_data["special_medical"],
            )
            event_reg.save()

            # Create Badge linked to staff profile with fandom_name
            badge_name = staff_profile.fandom_name or staff_profile.first_name()
            badge = Badge(
                staff=staff_profile,
                event=event,
                badgeName=badge_name,
                registeredDate=timezone.now(),
            )
            badge.save()

            # Get staff price level and create order item
            try:
                staff_price_level = PriceLevel.objects.filter(
                    available_to_staff=True,
                    startDate__lte=timezone.now(),
                    endDate__gte=timezone.now(),
                ).first()

                if staff_price_level:
                    order_item = OrderItem.objects.create(
                        badge=badge,
                        priceLevel=staff_price_level,
                        enteredBy="STAFF_PORTAL",
                    )
            except Exception:
                pass  # Continue even if order item creation fails

            # Rotate staff registration token for next year
            staff_profile.registration_token = get_registration_token()
            staff_profile.save()

            # If using StaffInvite token, mark it as used
            if is_invite_token and invite:
                invite.used = True
                invite.used_date = timezone.now()
                invite.save()

            return redirect("staff:register_complete")

    else:
        # Pre-fill form from staff profile
        initial_data = {
            "street_address_1": staff_profile.street_address_1,
            "street_address_2": staff_profile.street_address_2,
            "city": staff_profile.city,
            "state": staff_profile.state,
            "country": staff_profile.country,
            "postal_code": staff_profile.postal_code,
        }

        # Try to get last year's registration data
        last_reg = (
            StaffEventRegistration.objects.filter(staff=staff_profile)
            .exclude(event=event)
            .order_by("-event__eventStart")
            .first()
        )

        if last_reg:
            initial_data.update(
                {
                    "bluesky": last_reg.bluesky,
                    "telegram": last_reg.telegram,
                    "contact_name": last_reg.contact_name,
                    "contact_phone": last_reg.contact_phone,
                    "contact_relation": last_reg.contact_relation,
                    "special_skills": last_reg.special_skills,
                    "special_food": last_reg.special_food,
                    "special_medical": last_reg.special_medical,
                    # Note: NOT carrying over shirt size
                }
            )

        form = StaffRegistrationForm(initial=initial_data)

    context = {
        "form": form,
        "staff_profile": staff_profile,
        "event": event,
        "token": token,
    }
    return render(request, "staff/register.html", context)


def register_complete(request):
    """Registration completion page"""
    try:
        event = Event.objects.get(default=True)
    except Event.DoesNotExist:
        event = None

    return render(request, "staff/register_complete.html", {"event": event})
