from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from registration.models import get_registration_token
from staff.forms import StaffApplicationForm
from staff.models import StaffApplicant, StaffPosting


def index(request):
    """
    Redirect to appropriate page:
    - If user is authenticated and has a staff profile, redirect to portal
    - Otherwise, redirect to openings (public view)
    """
    if request.user.is_authenticated and hasattr(request.user, 'staff_profile'):
        return redirect('staff:portal')
    return redirect('staff:openings')


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
    return HttpResponse("Hello world - staff portal")
