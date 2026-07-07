from django import forms

from staff.models import StaffApplicant


class StaffApplicationForm(forms.ModelForm):
    class Meta:
        model = StaffApplicant
        fields = [
            "legal_first_name",
            "legal_last_name",
            "preferred_first_name",
            "preferred_last_name",
            "birthdate",
            "email",
            "phone",
            "street_address_1",
            "street_address_2",
            "city",
            "state",
            "country",
            "postal_code",
            "email_ok",
            "survey_ok",
        ]
        widgets = {
            "legal_first_name": forms.TextInput(attrs={"class": "form-control"}),
            "legal_last_name": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_first_name": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_last_name": forms.TextInput(attrs={"class": "form-control"}),
            "birthdate": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "street_address_1": forms.TextInput(attrs={"class": "form-control", "placeholder": "Street Address"}),
            "street_address_2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apt, Suite, etc. (optional)"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "email_ok": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "survey_ok": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "preferred_first_name": "Leave blank if same as legal name",
            "preferred_last_name": "Leave blank if same as legal name",
            "email_ok": "Can we contact you via email about future opportunities?",
            "survey_ok": "Can we send you surveys about your experience?",
        }
