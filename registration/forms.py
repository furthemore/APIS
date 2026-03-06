from typing import Any

from django import forms
from django.forms import ModelForm, ValidationError
from django.forms.widgets import TextInput

from .models import Attendee, Badge, Event, Firebase, Order

COUNTRIES_REQUIRING_STATE = ("US",)


def check_state(data: dict, country_field: str, state_field: str):
    country = data.get(country_field)
    state = data.get(state_field)
    if country in COUNTRIES_REQUIRING_STATE and not state:
        raise ValidationError(
            {
                state_field: ValidationError(
                    f"State is required in {country}", code="required"
                ),
            }
        )


class FirebaseForm(ModelForm):
    class Meta:
        model = Firebase
        fields = (
            "name",
            "token",
            "cashdrawer",
            "payment_type",
            "square_terminal_id",
            "print_via_mqtt",
            "print_via_payment",
            "webview",
            "background_color",
        )
        widgets = {
            "foreground_color": TextInput(attrs={"type": "color"}),
            "background_color": TextInput(attrs={"type": "color"}),
        }


class SignatureUploadForm(forms.Form):
    badge_id = forms.IntegerField()
    svg_file = forms.FileField()
    png_file = forms.FileField()


class AttendeeForm(forms.ModelForm):
    def __init__(self, collect_address: bool, **kwargs) -> None:
        super().__init__(**kwargs)

        if collect_address:
            for field in AttendeeForm.Meta.required_address_fields:
                self.fields[field].required = True

    @classmethod
    def from_pda(cls, pda: dict, event: Event) -> "AttendeeForm":
        return cls(
            collect_address=event.collectAddress,
            data={
                "firstName": pda.get("firstName"),
                "preferredName": pda.get("preferredName"),
                "lastName": pda.get("lastName"),
                "phone": pda.get("phone"),
                "email": pda.get("email"),
                "address1": pda.get("address1"),
                "address2": pda.get("address2"),
                "city": pda.get("city"),
                "state": pda.get("state"),
                "country": pda.get("country"),
                "postalCode": pda.get("postal"),
                "birthdate": pda.get("birthdate"),
                "emailsOk": pda.get("emailsOk"),
                "surveyOk": pda.get("surveyOk"),
                "volunteerContact": len(pda.get("volDeps", "")) > 0,
                "volunteerDepts": pda.get("volDeps"),
                "aslRequest": pda.get("asl"),
            },
        )

    def clean(self) -> dict[str, Any]:
        data = super().clean()
        check_state(data, "country", "state")
        return data

    class Meta:
        model = Attendee

        required_address_fields = (
            "address1",
            "city",
            "country",
            "postalCode",
        )

        fields = (
            "firstName",
            "preferredName",
            "lastName",
            "phone",
            "email",
            "birthdate",
            "emailsOk",
            "surveyOk",
            "volunteerContact",
            "volunteerDepts",
            "aslRequest",
            "address2",
            "state",
        ) + required_address_fields


class BadgeForm(forms.ModelForm):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.fields["badgeName"].required = True

    class Meta:
        model = Badge
        fields = ("badgeName", "signature_svg", "signature_bitmap")


class OrderForm(forms.ModelForm):
    def __init__(self, collect_billing_address: bool, **kwargs) -> None:
        super().__init__(**kwargs)

        self.fields["apiData"].required = False

        if collect_billing_address:
            for field in OrderForm.Meta.required_billing_fields:
                self.fields[field].required = True

    def clean(self) -> dict[str, Any]:
        data = super().clean()
        check_state(data, "billingCountry", "billingState")
        return data

    class Meta:
        model = Order

        required_billing_fields = (
            "billingName",
            "billingAddress1",
            "billingCity",
            "billingCountry",
            "billingEmail",
            "billingPostal",
        )

        fields = (
            "total",
            "reference",
            "discount",
            "orgDonation",
            "charityDonation",
            "apiData",
            "billingAddress2",
            "billingState",
        ) + required_billing_fields
