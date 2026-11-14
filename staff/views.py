from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

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


@require_GET
def index(request):
    """
    Redirect to appropriate page:
    - If user is authenticated and has a staff profile, redirect to portal
    - Otherwise, redirect to openings (public view)
    """
    if request.user.is_authenticated and hasattr(request.user, "staff_profile"):
        return redirect("staff:portal")
    return redirect("staff:openings")


def _get_current_event():
    """Return the default event, or None if there isn't one."""
    return Event.objects.filter(default=True).first()


def _get_event_registration(staff, event):
    """Return the staff member's registration for the event, if any."""
    if not event:
        return None
    return StaffEventRegistration.objects.filter(staff=staff, event=event).first()


def _build_staff_list(department, event):
    """
    List direct members of a department with their registration status.
    Registrations are fetched in a single query rather than one per member.
    """
    members = list(Staff.objects.filter(department=department).select_related("user"))
    registrations = {}
    if event:
        registrations = {
            reg.staff_id: reg
            for reg in StaffEventRegistration.objects.filter(
                staff__in=members, event=event
            )
        }

    staff_list = []
    for member in members:
        registration = registrations.get(member.pk)
        staff_list.append(
            {
                "staff": member,
                "is_registered": registration is not None,
                "checked_in": registration.checked_in if registration else False,
            }
        )
    return staff_list


def _count_registered(department, event):
    """Count staff in the department registered for the event."""
    if not event:
        return 0
    return StaffEventRegistration.objects.filter(
        staff__department=department, event=event
    ).count()


def _build_sub_department_stats(department, event):
    stats = []
    for sub_dept in department.sub_departments.all():
        stats.append(
            {
                "department": sub_dept,
                "staff_count": Staff.objects.filter(department=sub_dept).count(),
                "registered_count": _count_registered(sub_dept, event),
                "staff_list": _build_staff_list(sub_dept, event),
            }
        )
    return stats


def _build_department_stats(department, event):
    return {
        "department": department,
        "direct_staff_count": Staff.objects.filter(department=department).count(),
        "total_staff": department.get_all_staff().count(),
        "registered_count": _count_registered(department, event),
        "staff_list": _build_staff_list(department, event),
        "sub_departments": _build_sub_department_stats(department, event),
    }


@login_required
@require_GET
def profile(request):
    """
    Staff profile view - shows different content based on role:
    - Department heads/assistant heads: Dashboard with department stats
    - Regular staff: Personal profile summary
    """
    if not hasattr(request.user, "staff_profile"):
        return render(
            request,
            "staff/profile_no_access.html",
            {
                "message": "You do not have a staff profile. Please contact an administrator."
            },
        )

    staff_profile = request.user.staff_profile
    current_event = _get_current_event()
    registration_token = staff_profile.registration_token if current_event else None
    event_registration = _get_event_registration(staff_profile, current_event)

    context = {
        "staff_profile": staff_profile,
        "current_event": current_event,
        "registration_token": registration_token,
        "is_registered": event_registration is not None,
        "registration_record": event_registration,
        "is_department_leader": False,
    }

    led_departments = Department.objects.filter(
        models.Q(heads=staff_profile) | models.Q(assistant_heads=staff_profile)
    ).distinct()

    if not led_departments.exists():
        return render(request, "staff/profile_staff.html", context)

    context["is_department_leader"] = True
    context["department_stats"] = [
        _build_department_stats(dept, current_event) for dept in led_departments
    ]
    return render(request, "staff/profile_leader.html", context)


@require_GET
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


@require_http_methods(["GET", "POST"])
def apply(request, token):
    """Application form for a specific posting."""
    posting = get_object_or_404(
        StaffPosting.objects.select_related(
            "position", "position__department", "event"
        ),
        token=token,
        is_open=True,
    )

    if request.method == "POST":
        form = StaffApplicationForm(request.POST)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.posting = posting
            applicant.registration_token = get_registration_token()
            applicant.save()
            return redirect("staff:application", token=applicant.registration_token)
    else:
        form = StaffApplicationForm()

    context = {
        "posting": posting,
        "form": form,
    }
    return render(request, "staff/apply.html", context)


@require_GET
def application(request, token):
    """Confirmation page after submitting an application."""
    applicant = get_object_or_404(
        StaffApplicant.objects.select_related("posting", "posting__position"),
        registration_token=token,
    )

    context = {
        "applicant": applicant,
    }
    return render(request, "staff/application.html", context)


@require_http_methods(["GET", "POST"])
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


@require_GET
def register_complete(request):
    """Registration completion page"""
    try:
        event = Event.objects.get(default=True)
    except Event.DoesNotExist:
        event = None

    return render(request, "staff/register_complete.html", {"event": event})
