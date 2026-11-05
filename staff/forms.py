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
            "birthdate": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "street_address_1": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Street Address"}
            ),
            "street_address_2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Apt, Suite, etc. (optional)",
                }
            ),
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


class StaffRegistrationForm(forms.Form):
    """Form for staff event registration - pulls data from staff profile"""

    # Address fields (editable)
    street_address_1 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Street Address"}
        ),
    )
    street_address_2 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Apt, Suite, etc. (optional)",
            }
        ),
    )
    city = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    state = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    country = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    postal_code = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    # Shirt size (editable)
    shirt_size = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    # Social media handles (editable)
    bluesky = forms.CharField(
        label="Bluesky Handle",
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "@username.bsky.social"}
        ),
    )
    telegram = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "@username"}
        ),
    )

    # Emergency contact (editable)
    contact_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    contact_phone = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    contact_relation = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g., Spouse, Parent, Friend",
            }
        ),
    )

    # Special needs (editable)
    special_skills = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    special_food = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    special_medical = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate shirt size choices
        from registration.models import ShirtSizes

        self.fields["shirt_size"].queryset = ShirtSizes.objects.all()
