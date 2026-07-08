from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from registration.models import Event, get_registration_token, Staff as RegistrationStaff, Attendee, Badge, ShirtSizes, PriceLevel, OrderItem
from registration.views.ordering import CreateAttendeeOptions
from staff.forms import StaffApplicationForm, StaffRegistrationForm
from staff.models import Department, StaffApplicant, StaffPosting, Staff, StaffInvite


def index(request):
    """
    Redirect to appropriate page:
    - If user is authenticated and has a staff profile, redirect to portal
    - Otherwise, redirect to openings (public view)
    """
    if request.user.is_authenticated and hasattr(request.user, 'staff_profile'):
        return redirect('staff:portal')
    return redirect('staff:openings')


@login_required
def profile(request):
    """
    Staff profile view - shows different content based on role:
    - Department heads/assistant heads: Dashboard with department stats
    - Regular staff: Personal profile summary
    """
    # Check if user has a staff profile
    if not hasattr(request.user, 'staff_profile'):
        return render(request, 'staff/profile_no_access.html', {
            'message': 'You do not have a staff profile. Please contact an administrator.'
        })
    
    staff_profile = request.user.staff_profile
    
    # Get current/default event
    try:
        current_event = Event.objects.get(default=True)
    except Event.DoesNotExist:
        current_event = None
    
    # Check if user is a department head or assistant head
    is_department_leader = Department.objects.filter(
        heads=staff_profile
    ).exists() or Department.objects.filter(
        assistant_heads=staff_profile
    ).exists()
    
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
            
            # Count how many are registered for current event (have registration.Staff record)
            registered_count = 0
            if current_event:
                registered_count = RegistrationStaff.objects.filter(
                    department=dept,
                    event=current_event
                ).count()
            
            # Get staff list with their registration status (direct members only)
            staff_list = []
            for staff_member in Staff.objects.filter(department=dept).select_related('user'):
                # Check if they're registered for current event
                is_registered = False
                registration_record = None
                if current_event and staff_member.user:
                    # Try to find their registration.Staff record via attendee
                    try:
                        attendee = staff_member.user.attendee_set.first()
                        if attendee:
                            registration_record = RegistrationStaff.objects.filter(
                                attendee=attendee,
                                event=current_event
                            ).first()
                            is_registered = registration_record is not None
                    except:
                        pass
                
                staff_list.append({
                    'staff': staff_member,
                    'is_registered': is_registered,
                    'checked_in': registration_record.checkedIn if registration_record else False,
                })
            
            # Get sub-departments with their stats
            sub_dept_stats = []
            for sub_dept in dept.sub_departments.all():
                sub_staff_count = Staff.objects.filter(department=sub_dept).count()
                sub_registered_count = 0
                if current_event:
                    sub_registered_count = RegistrationStaff.objects.filter(
                        department=sub_dept,
                        event=current_event
                    ).count()
                
                # Get staff list for sub-department
                sub_staff_list = []
                for staff_member in Staff.objects.filter(department=sub_dept).select_related('user'):
                    # Check if they're registered for current event
                    is_registered = False
                    registration_record = None
                    if current_event and staff_member.user:
                        try:
                            attendee = staff_member.user.attendee_set.first()
                            if attendee:
                                registration_record = RegistrationStaff.objects.filter(
                                    attendee=attendee,
                                    event=current_event
                                ).first()
                                is_registered = registration_record is not None
                        except:
                            pass
                    
                    sub_staff_list.append({
                        'staff': staff_member,
                        'is_registered': is_registered,
                        'checked_in': registration_record.checkedIn if registration_record else False,
                    })
                
                sub_dept_stats.append({
                    'department': sub_dept,
                    'staff_count': sub_staff_count,
                    'registered_count': sub_registered_count,
                    'staff_list': sub_staff_list,
                })
            
            department_stats.append({
                'department': dept,
                'direct_staff_count': direct_staff_count,
                'total_staff': total_staff,
                'registered_count': registered_count,
                'staff_list': staff_list,
                'sub_departments': sub_dept_stats,
            })
        
        context = {
            'staff_profile': staff_profile,
            'is_department_leader': True,
            'current_event': current_event,
            'department_stats': department_stats,
        }
        return render(request, 'staff/profile_leader.html', context)
    
    else:
        # Regular staff member - show personal summary
        # Check if they're registered for current event
        is_registered = False
        registration_record = None
        if current_event and request.user:
            try:
                attendee = request.user.attendee_set.first()
                if attendee:
                    registration_record = RegistrationStaff.objects.filter(
                        attendee=attendee,
                        event=current_event
                    ).first()
                    is_registered = registration_record is not None
            except:
                pass
        
        context = {
            'staff_profile': staff_profile,
            'is_department_leader': False,
            'current_event': current_event,
            'is_registered': is_registered,
            'registration_record': registration_record,
        }
        return render(request, 'staff/profile_staff.html', context)


def openings(request):
    """List all open staff postings."""
    postings = StaffPosting.objects.filter(is_open=True).select_related(
        "position", "position__department", "event"
    ).order_by("position__position_type", "position__title")
    
    context = {
        "postings": postings,
    }
    return render(request, "staff/openings.html", context)


def apply(request, posting_id):
    """Application form for a specific posting."""
    posting = get_object_or_404(
        StaffPosting.objects.select_related("position", "position__department", "event"),
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


def portal(request):
    """Portal redirects to profile view"""
    return redirect('staff:profile')
