import copy
import html
import json
import logging
from datetime import date
from io import BytesIO

import qrcode
from django import forms
from django.conf.urls import url
from django.contrib import admin, auth, messages
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.signing import TimestampSigner
from django.db import transaction
from django.db.models import Max
from django.forms import NumberInput, widgets
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html, urlencode
from django.utils.safestring import mark_safe
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from nested_inline.admin import NestedModelAdmin, NestedTabularInline
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer
from qrcode.image.svg import SvgPathFillImage

import registration.emails
import registration.views.printing
from registration import mqtt, payments
from registration.forms import FirebaseForm
from registration.models import *
from registration.pushy import PushyAPI, PushyError

from . import printing

logger = logging.getLogger(__name__)

TWOPLACES = Decimal(10) ** -2

admin.site.site_url = None
admin.site.site_header = "APIS Backoffice"

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Charity)
admin.site.register(TableSize)
admin.site.register(Cart)


def disable_two_factor(modeladmin, request, queryset):
    for user in queryset:
        obj = user.totp_devices.filter(user=user)
        obj.delete()
        obj = user.u2f_keys.filter(user=user)
        obj.delete()
        obj = user.backup_codes.filter(user=user)
        obj.delete()


disable_two_factor.short_description = "Disable 2FA"


class UserProfileAdmin(auth.admin.UserAdmin):
    model = User
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "two_factor_enabled",
    )
    actions = [
        disable_two_factor,
    ]

    def two_factor_enabled(self, obj):
        return obj.totp_devices.first() is not None or obj.u2f_keys.first() is not None

    two_factor_enabled.boolean = True
    two_factor_enabled.short_description = "2FA"


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)


class FirebaseAdmin(admin.ModelAdmin):
    list_display = ("name", "token", "closed")
    form = FirebaseForm

    def render_change_form(self, request, context, *args, **kwargs):
        obj = kwargs.get("obj")

        return super(FirebaseAdmin, self).render_change_form(
            request, context, *args, **kwargs
        )

    def get_urls(self):
        urls = super(FirebaseAdmin, self).get_urls()
        my_urls = [
            url(r"^(.+)/provision/$", self.provision_view, name="firebase_provision"),
        ]
        return my_urls + urls

    def save_model(self, request, obj, form, change):
        obj.save()
        data = {
            "command": "settings",
            "json": self.get_provisioning(obj, closed=obj.closed),
        }

        try:
            PushyAPI.send_push_notification(data, [obj.token], None)
        except PushyError as e:
            messages.warning(
                request,
                f"We tried to update the terminal's settings, but there was a problem: {e}",
            )

    @staticmethod
    def get_provisioning(firebase, **kwargs):
        current_site = Site.objects.get_current()
        endpoint = settings.REGISTER_ENDPOINT
        if endpoint is None:
            endpoint = "https://{0}{1}".format(current_site.domain, reverse("root"))

        document = {
            "v": 1,
            "client_id": settings.SQUARE_APPLICATION_ID,
            "api_key": settings.REGISTER_KEY,
            "endpoint": endpoint,
            "name": firebase.name,
            "location_id": settings.REGISTER_SQUARE_LOCATION,
            "force_location": settings.REGISTER_FORCE_LOCATION,
            "bg": firebase.background_color,
            "fg": firebase.foreground_color,
            "webview": firebase.webview,
        }
        document.update(kwargs)

        return json.dumps(document)

    @staticmethod
    def get_qrcode(data):
        img = qrcode.make(data, image_factory=SvgPathFillImage)
        buf = BytesIO()
        img.save(buf)
        return buf.getvalue()

    def provision_view(self, request, pk):
        obj = Firebase.objects.get(id=pk)
        provisioning = self.get_provisioning(obj)
        token = mqtt.get_client_token(obj)

        context = {
            "qr_svg": self.get_qrcode(provisioning).decode("utf-8"),
            "token": token,
        }

        return render(request, "admin/firebase_qr.html", context)


admin.site.register(Firebase, FirebaseAdmin)


class BanListAdmin(admin.ModelAdmin):
    list_display = ("firstName", "lastName", "email", "reason")


admin.site.register(BanList, BanListAdmin)


def send_staff_token_email(modeladmin, request, queryset):
    if queryset.count() == 0:
        messages.error("Invalid token selected")
        return

    for token in queryset:
        registration.emails.send_new_staff_email(token)
        token.sent = True
        token.save()
    if queryset.count() > 1:
        messages.success(
            request, "Successfully sent emails to %d staff members" % queryset.count()
        )
    else:
        messages.success(request, "Successfully sent email to %s" % queryset[0])


send_staff_token_email.short_description = "Send New Staff registration email"


class TempTokenAdmin(admin.ModelAdmin):
    actions = [send_staff_token_email]
    list_display = ["email", "token", "sent", "used"]


admin.site.register(TempToken, TempTokenAdmin)


def send_approval_email(modeladmin, request, queryset):
    registration.emails.send_dealer_approval_email(queryset)
    queryset.update(emailed=True)
    if queryset.count() > 1:
        messages.success(request, "Successfully emailed %d dealers" % queryset.count())
    else:
        messages.success(request, "Successfully emailed %s" % queryset[0].attendee)


send_approval_email.short_description = "Send approval email and payment instructions"


def mark_as_approved(modeladmin, request, queryset):
    for dealer in queryset:
        dealer.approved = True
        dealer.save()
    if queryset.count() > 1:
        messages.success(request, "Successfully approved %d dealers" % queryset.count())
    else:
        messages.success(request, "Successfully approved %s" % queryset[0].attendee)


mark_as_approved.short_description = "Approve selected dealers"


def send_payment_email(modeladmin, request, queryset):
    for dealer in queryset:
        badge = dealer.getBadge()
        oi = OrderItem.objects.filter(badge=badge).first()
        if oi and oi.order:
            registration.emails.send_dealer_payment_email(dealer, oi.order)
    if queryset.count() > 1:
        messages.success(request, "Successfully emailed %d dealers" % queryset.count())
    else:
        messages.success(request, "Successfully emailed %s" % queryset[0].attendee)


send_payment_email.short_description = "Resend payment confirmation email"


def send_assistant_form_email(modeladmin, request, queryset):
    for dealer in queryset:
        registration.emails.send_dealer_assistant_form_email(dealer)
    if queryset.count() > 1:
        messages.success(request, "Successfully emailed %d dealers" % queryset.count())
    else:
        messages.success(request, "Successfully emailed %s" % queryset[0].attendee)


send_assistant_form_email.short_description = "Send assistant addition form email"


class DealerAsstInline(NestedTabularInline):
    model = DealerAsst
    extra = 0


class DealerAsstResource(resources.ModelResource):
    badgeName = fields.Field()

    class Meta:
        model = DealerAsst
        fields = (
            "id",
            "name",
            "badgeName",
            "email",
            "license",
            "event__name",
            "dealer__businessName",
            "dealer__attendee__email",
            "dealer__approved",
            "dealer__tableNumber",
        )
        export_order = (
            "id",
            "name",
            "badgeName",
            "email",
            "license",
            "event__name",
            "dealer__businessName",
            "dealer__attendee__email",
            "dealer__approved",
            "dealer__tableNumber",
        )

    def dehydrate_badgeName(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.badgeName


def send_assistant_registration_email(modeladmin, request, queryset):
    for assistant in queryset:
        registration.emails.send_dealer_assistant_registration_invite(assistant)
    if queryset.count() > 1:
        messages.success(
            request,
            "Successfully sent emails to %d dealer assistants" % queryset.count(),
        )
    else:
        messages.success(
            request, "Successfully sent email to %s" % queryset[0].attendee
        )


send_assistant_registration_email.short_description = "Send registration instructions"


class DealerAsstAdmin(ImportExportModelAdmin):
    save_on_top = True
    list_display = (
        "name",
        "email",
        "license",
        "event",
        "dealer_businessname",
        "dealer_approved",
        "paid",
        "sent",
        "asst_registered",
    )
    list_filter = ("event", "dealer__approved", "paid")
    list_select_related = ("event", "dealer", "attendee")
    search_fields = ["name", "email"]
    readonly_fields = ["dealer_businessname", "dealer_approved", "registrationToken"]
    resource_class = DealerAsstResource
    raw_id_fields = ("dealer", "attendee")
    actions = [
        send_assistant_registration_email,
    ]

    def dealer_businessname(self, obj):
        return obj.dealer.businessName

    def dealer_approved(self, obj):
        return obj.dealer.approved

    dealer_approved.boolean = True

    def asst_registered(self, obj):
        if obj.attendee is not None:
            return True
        else:
            return False

    asst_registered.boolean = True
    asst_registered.short_description = "Assistant Registered"


admin.site.register(DealerAsst, DealerAsstAdmin)


class DealerResource(resources.ModelResource):
    badgeName = fields.Field()

    class Meta:
        model = Dealer
        fields = (
            "id",
            "event__name",
            "badgeName",
            "attendee__firstName",
            "attendee__lastName",
            "attendee__address1",
            "attendee__address2",
            "attendee__city",
            "attendee__state",
            "attendee__country",
            "attendee__postalCode",
            "attendee__phone",
            "attendee__email",
            "businessName",
            "approved",
            "tableNumber",
            "website",
            "description",
            "license",
            "needPower",
            "needWifi",
            "chairs",
            "tables",
            "wallSpace",
            "nearTo",
            "farFrom",
            "tableSize__name",
            "reception",
            "artShow",
            "charityRaffle",
            "breakfast",
            "asstBreakfast",
            "willSwitch",
            "buttonOffer",
            "discount",
            "discountReason",
            "emailed",
        )
        export_order = (
            "id",
            "event__name",
            "badgeName",
            "attendee__firstName",
            "attendee__lastName",
            "attendee__address1",
            "attendee__address2",
            "attendee__city",
            "attendee__state",
            "attendee__country",
            "attendee__postalCode",
            "attendee__phone",
            "attendee__email",
            "businessName",
            "approved",
            "tableNumber",
            "website",
            "description",
            "license",
            "needPower",
            "needWifi",
            "chairs",
            "tables",
            "wallSpace",
            "nearTo",
            "farFrom",
            "tableSize__name",
            "reception",
            "artShow",
            "charityRaffle",
            "breakfast",
            "asstBreakfast",
            "willSwitch",
            "buttonOffer",
            "discount",
            "discountReason",
            "emailed",
        )

    def dehydrate_badgeName(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.badgeName


class DealerAdmin(NestedModelAdmin, ImportExportModelAdmin):
    list_display = (
        "attendee",
        "businessName",
        "tableSize",
        "chairs",
        "tables",
        "needWifi",
        "approved",
        "tableNumber",
        "emailed",
        "paidTotal",
        "event",
    )
    list_filter = ("event", "approved", "emailed")
    list_select_related = ("tableSize", "event", "attendee")
    save_on_top = True
    inlines = [DealerAsstInline]
    resource_class = DealerResource
    actions = [
        mark_as_approved,
        send_approval_email,
        send_assistant_form_email,
        send_payment_email,
    ]
    readonly_fields = ["get_email", "registrationToken", "get_badge"]
    raw_id_fields = ("attendee",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("attendee", "approved"),
                    ("get_email", "get_badge"),
                    ("registrationToken", "event"),
                    "tableNumber",
                    ("discount", "discountReason"),
                    "notes",
                )
            },
        ),
        (
            "Business Info",
            {"fields": ("businessName", "license", "website", "logo", "description")},
        ),
        (
            "Table Request",
            {
                "fields": (
                    "tableSize",
                    (
                        "willSwitch",
                        "needPower",
                        "needWifi",
                        "wallSpace",
                        "reception",
                        "breakfast",
                    ),
                    ("nearTo", "farFrom"),
                    ("tables", "chairs"),
                    "asstBreakfast",
                )
            },
        ),
        ("Contributions", {"fields": ("artShow", "buttonOffer", "charityRaffle")}),
    )

    def get_email(self, obj):
        if obj.attendee:
            return obj.attendee.email
        return "--"

    get_email.short_description = "Attendee Email"

    def get_badge(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.badgeName

    get_badge.short_description = "Badge Name"


admin.site.register(Dealer, DealerAdmin)


class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "eventStart", "eventEnd", "default")
    fieldsets = (
        (
            "Basic Event Info",
            {
                "fields": (
                    "default",
                    "name",
                    "websiteUrl",
                    "eventStart",
                    "eventEnd",
                    "venue",
                    "charity",
                    "donations",
                    ("codeOfConduct", "badgeTheme", "defaultBadgeTemplate"),
                )
            },
        ),
        (
            "Registration Timing",
            {
                #'classes': ('wide', ),
                "fields": (
                    ("attendeeRegStart", "attendeeRegEnd"),
                    ("onsiteRegStart", "onsiteRegEnd"),
                    ("staffRegStart", "staffRegEnd"),
                    ("dealerRegStart", "dealerRegEnd"),
                )
            },
        ),
        (
            "Online Registration Options",
            {
                "fields": (
                    "collectAddress",
                    "collectBillingAddress",
                    "allowOnlineMinorReg",
                )
            },
        ),
        (
            "Contact Email Addresses",
            {
                "fields": (
                    "registrationEmail",
                    "staffEmail",
                    "dealerEmail",
                )
            },
        ),
        (
            "Discounts",
            {
                "classes": ("collapse",),
                "fields": (
                    "staffDiscount",
                    "newStaffDiscount",
                    "dealerDiscount",
                    "assistantDiscount",
                ),
            },
        ),
        (
            "Dealers Configuration",
            {
                "classes": ("collapse",),
                "fields": (
                    "dealerWifi",
                    "dealerWifiPrice",
                    "dealerPartnerPrice",
                ),
            },
        ),
    )


admin.site.register(Event, EventAdmin)

########################################################
#   Staff Admin


def checkin_staff(modeladmin, request, queryset):
    for staff in queryset:
        staff.checkedIn = True
        staff.save()


checkin_staff.short_description = "Check in staff"


def send_staff_registration_email(modeladmin, request, queryset):
    for staff in queryset:
        registration.emails.send_staff_promotion_email(staff)


send_staff_registration_email.short_description = "Send registration instructions"


class StaffResource(resources.ModelResource):
    badgeName = fields.Field()

    class Meta:
        model = Staff
        fields = (
            "id",
            "event__name",
            "badgeName",
            "attendee__preferredName",
            "attendee__firstName",
            "attendee__lastName",
            "attendee__address1",
            "attendee__address2",
            "attendee__city",
            "attendee__state",
            "attendee__country",
            "attendee__postalCode",
            "attendee__phone",
            "attendee__email",
            "department__name",
            "supervisor",
            "title",
            "twitter",
            "telegram",
            "shirtsize__name",
            "specialSkills",
            "specialFood",
            "specialMedical",
            "contactName",
            "contactPhone",
            "contactRelation",
        )
        export_order = (
            "id",
            "event__name",
            "badgeName",
            "attendee__preferredName",
            "attendee__firstName",
            "attendee__lastName",
            "attendee__address1",
            "attendee__address2",
            "attendee__city",
            "attendee__state",
            "attendee__country",
            "attendee__postalCode",
            "attendee__phone",
            "attendee__email",
            "department__name",
            "supervisor",
            "title",
            "twitter",
            "telegram",
            "shirtsize__name",
            "specialSkills",
            "specialFood",
            "specialMedical",
            "contactName",
            "contactPhone",
            "contactRelation",
        )

    def dehydrate_badgeName(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.badgeName


class StaffAdmin(ImportExportModelAdmin):
    save_on_top = True
    actions = [send_staff_registration_email, checkin_staff, "copy_to_event"]
    raw_id_fields = ("attendee",)
    list_display = (
        "attendee",
        "get_badge",
        "get_email",
        "title",
        "department",
        "shirtsize",
        "staff_total",
        "checkedIn",
        "event",
    )
    list_filter = ("event", "department")
    list_select_related = ("attendee", "department", "shirtsize", "event")
    search_fields = [
        "attendee__email",
        "attendee__lastName",
        "attendee__firstName",
        "attendee__preferredName",
    ]
    resource_class = StaffResource
    readonly_fields = ["get_email", "get_badge", "get_badge_id", "registrationToken"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("attendee", "registrationToken"),
                    ("event", "get_email"),
                    ("get_badge", "get_badge_id"),
                    ("title", "department"),
                    ("twitter", "telegram"),
                    ("shirtsize", "checkedIn"),
                )
            },
        ),
        (
            "Emergency Contact",
            {"fields": ("contactName", "contactPhone", "contactRelation")},
        ),
        (
            "Misc",
            {"fields": ("specialSkills", "specialFood", "specialMedical", "notes")},
        ),
    )

    def get_email(self, obj):
        if obj.attendee:
            return obj.attendee.email
        return "--"

    get_email.short_description = "Email"

    def get_badge(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.badgeName

    get_badge.short_description = "Badge Name"

    def get_badge_id(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.badgeNumber

    get_badge_id.short_description = "Badge Number"

    def staff_total(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge is None:
            return "--"
        return badge.paidTotal()

    class CopyToEvent(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        event = forms.ModelChoiceField(Event.objects)

    def copy_to_event(self, request, queryset):
        form = None

        if "event" in request.POST:
            form = self.CopyToEvent(request.POST)

            if form.is_valid():
                event = form.cleaned_data["event"]
                count = 0

                for staff in queryset:
                    if staff.event == event:
                        continue  # Don't copy staff to the same destination event

                    staff_copy = copy.copy(staff)
                    staff_copy.id = None
                    staff_copy.attendee = staff.attendee
                    staff_copy.event = event
                    staff_copy.registrationToken = getRegistrationToken()
                    staff_copy.shirtsize = None
                    staff_copy.checkedIn = False
                    staff_copy.save()
                    count += 1

                self.message_user(
                    request, "Successfully copied %d staff to %s." % (count, event)
                )
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.CopyToEvent(
                initial={"_selected_action": queryset.values_list("pk", flat=True)}
            )

        return render(
            request, "admin/copy_event.html", {"staff": queryset, "form": form}
        )

    copy_to_event.short_description = "Copy to Event..."


admin.site.register(Staff, StaffAdmin)


########################################################
#   Attendee/Badge Admin


def make_staff(modeladmin, request, queryset):
    event = Event.objects.get(default=True)
    skipped = 0
    for att in queryset:
        if Staff.objects.filter(attendee=att, event=event).exists():
            skipped += 1
            continue
        staff = Staff(attendee=att, event=event)
        staff.save()
    if queryset.count() > 1:
        if skipped > 0:
            messages.success(
                request,
                f"{queryset.count() - skipped} attendees added to staff ({skipped} ommited that were already on staff for {event})",
            )
        else:
            messages.success(
                request, f"{queryset.count()} attendees added to staff for {event}"
            )
    else:
        messages.success(
            request, f"Successfully added {queryset[0]} to staff for {event}"
        )


make_staff.short_description = "Add to Staff"


def send_upgrade_form_email(modeladmin, request, queryset):
    for badge in queryset:
        registration.emails.send_upgrade_instructions(badge)
    if queryset.count() > 1:
        messages.success(
            request, "Successfully sent emails to %d attendees" % queryset.count()
        )
    else:
        messages.success(request, "Successfully sent email to %s" % queryset[0])


send_upgrade_form_email.short_description = "Send upgrade info email"


def resend_confirmation_email(modeladmin, request, queryset):
    for badge in queryset:
        order = badge.getOrder()
        registration.emails.send_registration_email(
            order, badge.attendee.email, send_vip=False
        )
    if queryset.count() > 1:
        messages.success(
            request, "Successfully sent emails to %d attendees" % queryset.count()
        )
    else:
        messages.success(request, "Successfully sent email to %s" % queryset[0])


resend_confirmation_email.short_description = "Resend confirmation email"


@transaction.atomic
def assign_badge_numbers(modeladmin, request, queryset):
    first_badge = queryset[0]
    event = first_badge.event or Event.objects.get(default=True)
    badges = Badge.objects.filter(event=event)
    highest = Badge.objects.filter(event=event, badgeNumber__isnull=False).aggregate(
        Max("badgeNumber")
    )["badgeNumber__max"]
    if highest is None:
        highest = 0

    for badge in queryset.order_by("registeredDate"):
        # skip assigning to badges not in current event
        if badge not in badges:
            messages.warning(
                request,
                f"skipped assinging {badge} a number beacuse it is outside of current event",
            )
            continue

        # Skip badges which have already been assigned
        if badge.badgeNumber is not None:
            continue
        # Skip badges that are not assigned a registration level
        level = badge.effectiveLevel()
        if level is None or level == Badge.UNPAID:
            messages.warning(
                request,
                f"skipped assinging {badge} a number beacuse it's registration level is {level}",
            )
            continue

        highest += 1

        badge.badgeNumber = highest
        badge.save()


assign_badge_numbers.short_description = "Assign badge number"


def assign_numbers_and_print(modeladmin, request, queryset):
    assign_badge_numbers(modeladmin, request, queryset)
    response = print_badges(modeladmin, request, queryset)
    return response


assign_numbers_and_print.short_description = "Assign Number and Print"


def get_attendee_age(attendee):
    born = attendee.birthdate
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age


def print_badges(modeladmin, request, queryset):
    if getattr(settings, "PRINT_RENDERER", "wkhtmltopdf") == "gotenberg":
        signer = TimestampSigner()
        data = signer.sign_object({
            "badge_ids": [badge.id for badge in queryset],
        })

        pdf_path = reverse("registration:pdf") + f"?data={data}"
    else:
        pdf_name = generate_badge_labels(queryset, request)
        pdf_path = reverse("registration:pdf") + f"?file={pdf_name}"


    response = HttpResponseRedirect(reverse("registration:print"))
    url_params = {"file": pdf_path, "next": request.get_full_path()}
    response["Location"] += "?{}".format(urlencode(url_params))
    return response


def generate_badge_labels(queryset, request):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        level = badge.effectiveLevel()
        if level is None or level == Badge.UNPAID:
            messages.warning(
                request,
                f"skipped printing {badge} a number beacuse it's registration level is {level}",
            )
            continue
        if badge.badgeNumber is None:
            badge_number = ""
        else:
            badge_number = "{:04}".format(badge.badgeNumber)

        badge_type = get_badge_type(badge)
        if badge_type == "Attendee":
            printed_badge_level = html.escape(str(badge.effectiveLevel()))
        elif badge_type == "Dealer":
            printed_badge_level = "Dealer"
        elif badge_type == "Staff":
            printed_badge_level = "Staff"

        tags.append(
            {
                "name": html.escape(badge.badgeName),
                "number": badge_number,
                "level": printed_badge_level,
                "title": "",
                "age": get_attendee_age(badge.attendee),
            }
        )

        badge.printed = True
        badge.save()

    if len(tags) == 0:
        messages.warning(request, "None of the selected badges can be printed.")
        return
    con.nametags(tags, theme=badge.event.badgeTheme)
    # serve up this file
    pdf_path = con.pdf.split("/")[-1]
    return pdf_path


print_badges.short_description = "Print Badges"


def get_badge_type(badge):
    # check if staff
    try:
        staff = Staff.objects.get(attendee=badge.attendee, event=badge.event)
    except Staff.DoesNotExist:
        pass
    else:
        return "Staff"
    # check if dealer
    try:
        dealers = Dealer.objects.get(attendee=badge.attendee, event=badge.event)
    except Dealer.DoesNotExist:
        pass
    else:
        return "Dealer"
    return "Attendee"


class AttendeeOptionInline(NestedTabularInline):
    model = AttendeeOptions
    extra = 0


class OrderItemInline(NestedTabularInline):
    fk_name = "order"
    model = OrderItem
    raw_id_fields = ("badge", "order")
    extra = 0
    inlines = [AttendeeOptionInline]
    list_display = ["priceLevel", "enteredBy"]
    readonly_fields = ("enteredBy",)


class OrderItemInlineBadge(OrderItemInline):
    fk_name = "badge"


class BadgeInline(NestedTabularInline):
    model = Badge
    fk_name = "attendee"
    extra = 0
    inlines = [OrderItemInlineBadge]
    list_display = [
        "event",
        "badgeName",
        "badgeNumber",
        "registrationToken",
        "registrationDate",
    ]
    readonly_fields = [
        "get_age_range",
        "registrationToken",
    ]

    def get_age_range(self, obj):
        born = obj.attendee.birthdate
        today = date.today()
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
        if age >= 18:
            return format_html("<span>18+</span>")
        return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')

    get_age_range.short_description = "Age Group"


class BadgeResource(resources.ModelResource):
    badge_level = fields.Field()

    def dehydrate_badge_level(self, badge):
        return badge.effectiveLevel()

    class Meta:
        model = Badge
        fields = (
            "id",
            "event__name",
            "printed",
            "badge_level",
            "registeredDate",
            "attendee__firstName",
            "attendee__lastName",
            "attendee__address1",
            "attendee__address2",
            "attendee__city",
            "attendee__state",
            "attendee__country",
            "attendee__postalCode",
            "attendee__phone",
            "attendee__email",
            "badgeName",
            "badgeNumber",
            "attendee__aslRequest",
            "attendee__emailsOk",
            "attendee__surveyOk",
        )
        export_order = (
            "id",
            "printed",
            "event__name",
            "badge_level",
            "registeredDate",
            "attendee__firstName",
            "attendee__lastName",
            "attendee__address1",
            "attendee__address2",
            "attendee__city",
            "attendee__state",
            "attendee__country",
            "attendee__postalCode",
            "attendee__phone",
            "attendee__email",
            "badgeName",
            "badgeNumber",
            "attendee__aslRequest",
            "attendee__emailsOk",
            "attendee__surveyOk",
        )


class PriceLevelFilter(admin.SimpleListFilter):
    title = "badge level"
    parameter_name = "badgelevel"

    def lookups(self, request, model_admin):
        priceLevels = PriceLevel.objects.all()
        return tuple((lvl.name, lvl.name) for lvl in priceLevels)

    def queryset(self, request, queryset):
        priceLevel = self.value()
        if priceLevel:
            return queryset.filter(orderitem__priceLevel__name=priceLevel)


class BadgeAdmin(NestedModelAdmin, ImportExportModelAdmin):
    list_per_page = 30
    inlines = [OrderItemInlineBadge]
    resource_class = BadgeResource
    save_on_top = True
    list_filter = ("event", "printed", PriceLevelFilter)
    list_select_related = ("event", "attendee")
    raw_id_fields = ("attendee",)
    list_display = (
        "attendee",
        "badgeName",
        "badgeNumber",
        "printed",
        "paidTotal",
        "effectiveLevel",
        "abandoned",
        "get_age_range",
        "registeredDate",
    )
    search_fields = [
        "attendee__email",
        "attendee__lastName",
        "attendee__firstName",
        "attendee__preferredName",
        "badgeName",
        "badgeNumber",
    ]
    readonly_fields = ["get_age_range", "registrationToken", "image_signature"]
    actions = [
        assign_badge_numbers,
        print_badges,
        assign_numbers_and_print,
        send_upgrade_form_email,
        resend_confirmation_email,
        "cull_abandoned_carts",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "printed",
                    ("badgeName", "badgeNumber", "get_age_range"),
                    ("registeredDate", "event", "registrationToken"),
                    "image_signature",
                    "attendee",
                )
            },
        ),
    )

    def image_signature(self, obj):
        return format_html('<img src="data:image/png;base64,{}">', obj.signature_bitmap)

    def get_age_range(self, obj):
        try:
            born = obj.attendee.birthdate
            today = date.today()
            age = (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )
            if age >= 18:
                return format_html("<span>18+</span>")
            return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')
        except BaseException:
            return "Invalid DOB"

    get_age_range.short_description = "Age Group"

    def cull_abandoned_carts(self, request, queryset):
        abandoned = [x for x in Badge.objects.filter() if x.abandoned == "Abandoned"]
        for obj in abandoned:
            obj.delete()
        self.message_user(
            request, "Removed {0} abandoned orders.".format(len(abandoned))
        )

    cull_abandoned_carts.short_description = "Cull Abandoned Carts (Use with caution!)"


admin.site.register(Badge, BadgeAdmin)


class AttendeeAdmin(NestedModelAdmin):
    inlines = [BadgeInline]
    save_on_top = True
    actions = [make_staff]
    search_fields = ["email", "lastName", "firstName", "preferredName"]
    list_display = ("getFirst", "lastName", "email", "get_age_range")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("preferredName", "firstName", "lastName"),
                    ("address1", "address2"),
                    ("city", "state", "postalCode", "country"),
                    ("email", "phone", "emailsOk", "surveyOk"),
                    "birthdate",
                )
            },
        ),
        (
            "Other Con Info",
            {"fields": ("aslRequest", "volunteerDepts", "holdType", "notes")},
        ),
        (
            "Parent Info",
            {
                "fields": (
                    "parentFirstName",
                    "parentLastName",
                    "parentPhone",
                    "parentEmail",
                )
            },
        ),
    )

    def get_age_range(self, obj):
        born = obj.birthdate
        today = date.today()
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
        if age >= 18:
            return format_html("<span>18+</span>")
        return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')

    get_age_range.short_description = "Age Group"


admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(AttendeeOptions)


class OrderItemAdmin(ImportExportModelAdmin):
    raw_id_fields = ("order", "badge")
    readonly_fields = ("enteredBy",)
    list_select_related = ("badge", "order")

    def save_model(self, request, obj, form, change):
        obj.enteredBy = request.user.username
        super().save_model(request, obj, form, change)


admin.site.register(OrderItem, OrderItemAdmin)


def send_registration_email(modeladmin, request, queryset):
    for order in queryset:
        registration.emails.send_registration_email(order, order.billingEmail)


send_registration_email.short_description = "Send registration email"


class OrderAdmin(ImportExportModelAdmin, NestedModelAdmin):
    list_display = (
        "reference",
        "createdDate",
        "total",
        "orgDonation",
        "charityDonation",
        "discount",
        "billingType",
        "status",
    )
    list_filter = ("status", "billingType")
    list_select_related = ("discount",)
    search_fields = ["reference", "lastFour"]
    readonly_fields = ("createdDate",)
    save_on_top = True
    inlines = [OrderItemInline]
    actions = [
        send_registration_email,
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("total", "billingType", "createdDate"),
                    ("reference", "status"),
                    ("discount", "lastFour"),
                    ("orgDonation", "charityDonation"),
                )
            },
        ),
        (
            "Billing Address",
            {
                "fields": (
                    "billingName",
                    "billingEmail",
                    "billingAddress1",
                    "billingAddress2",
                    "billingCity",
                    "billingState",
                    "billingPostal",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )

    def render_change_form(self, request, context, *args, **kwargs):
        obj = kwargs.get("obj")
        if obj and obj.billingType == Order.CREDIT:

            context["api_data"] = obj.apiData
            if not obj.apiData:
                messages.warning(
                    request,
                    f"Error while loading JSON from apiData field for this order: {obj}",
                )
                logger.warning(
                    f"Error while loading JSON from api_data for order {obj}",
                )
            else:
                if "dispute" in obj.apiData:
                    messages.warning(
                        request, "This transaction has been disputed by the cardholder"
                    )

        return super(OrderAdmin, self).render_change_form(
            request, context, *args, **kwargs
        )

    class RefundForm(forms.Form):
        amount = forms.DecimalField(
            min_value=0,
            decimal_places=2,
            widget=NumberInput(attrs={"size": "10", "style": "width: 70px"}),
        )
        reason = forms.CharField(
            widget=forms.TextInput(
                attrs={"size": "40", "maxlength": 192, "autofocus": "autofocus"}
            ),
            required=False,
        )

    def save_model(self, request, obj, form, change):
        if not request.user.has_perm("registration.issue_refund"):
            if form.data["status"] in (Order.REFUNDED, Order.REFUND_PENDING):
                status = Order.PENDING
                if obj.id:
                    status = Order.objects.get(id=obj.id).status
                messages.error(
                    request,
                    "You do not have permission to issue refunds. "
                    "The order status has been reverted to {0}".format(status),
                )
                obj.status = status
        obj.save()

    def refresh_view(self, request, order_id, extra_context=None):
        # Get Square Order ID, and grab latest info from the transactions API
        # Update status accordingly
        order = Order.objects.get(id=order_id)
        try:
            success, message = payments.refresh_payment(order)
        except ValueError as e:
            messages.error(
                request,
                "There was a problem while parsing the API data for this order: {0}".format(
                    e
                ),
            )
            return HttpResponseRedirect(
                reverse("admin:registration_order_change", args=(order_id,))
            )

        if success:
            messages.success(
                request, "Refreshed order information from Square successfully"
            )
        else:
            messages.error(
                request,
                "There was a problem while refreshing information about this order: {0}".format(
                    message
                ),
            )
        return HttpResponseRedirect(
            reverse("admin:registration_order_change", args=(order_id,))
        )

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        my_urls = [
            url(r"^(.+)/refund/$", self.refund_view, name="order_refund"),
            url(r"^(.+)/refresh/$", self.refresh_view, name="order_refresh"),
        ]
        return my_urls + urls

    def refund_view(self, request, order_id, extra_context=None):
        # TODO: Produce an error if a full refund has already been completed
        form = None

        order = Order.objects.get(id=order_id)

        api_data = order.apiData
        if not api_data and order.billingType == Order.CREDIT:
            messages.warning(request, "External payment data could not be decoded")

        if "amount" in request.POST:
            if not request.user.has_perm("registration.issue_refund"):
                messages.error(request, "You do not have permission to issue refunds.")
                return HttpResponseRedirect(request.get_full_path())

            form = self.RefundForm(request.POST)

            if form.is_valid():
                amount = Decimal(form.cleaned_data["amount"]).quantize(TWOPLACES)
                reason = form.cleaned_data.get("reason")

                if amount > order.total:
                    messages.error(
                        request,
                        "Refund amount (${0}) cannot exceed order total (${1})".format(
                            amount, order.total
                        ),
                    )
                else:
                    if reason is None:
                        reason = "[{0}]".format(request.user)
                    else:
                        reason += " [{0}]".format(request.user)
                    result, msg = payments.refund_payment(order, amount, reason)
                    if result:
                        messages.success(
                            request,
                            "{0} - refund amount: {1} (reason: {2})".format(
                                msg, amount, reason
                            ),
                        )
                    else:
                        messages.error(request, msg)
                    return HttpResponseRedirect(
                        reverse("admin:registration_order_change", args=(order_id,))
                    )
                return HttpResponseRedirect(request.get_full_path())
            else:
                messages.error(request, "Invalid form data.")

        if not form:
            form = self.RefundForm(initial={"amount": order.total})

        context = {
            "form": form,
            "order": order,
            "api_data": api_data,
        }

        return render(request, "admin/refund_form.html", context)


admin.site.register(Order, OrderAdmin)


class PriceLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "basePrice", "startDate", "endDate", "public", "group")


admin.site.register(PriceLevel, PriceLevelAdmin)


class PriceLevelOptionAdmin(admin.ModelAdmin):
    list_display = (
        "optionName",
        "rank",
        "optionPrice",
        "optionExtraType",
        "required",
        "active",
    )


admin.site.register(PriceLevelOption, PriceLevelOptionAdmin)


class DiscountAdmin(admin.ModelAdmin):
    list_display = ("codeName", "amountOff", "percentOff", "oneTime", "used", "status")
    save_on_top = True


admin.site.register(Discount, DiscountAdmin)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "volunteerListOk")


admin.site.register(Department, DepartmentAdmin)


class CashdrawerAdmin(ImportExportModelAdmin):
    list_display = ("timestamp", "action", "total", "tendered", "user", "position")
    list_select_related = ("user", "position")

    def save_model(self, request, obj, form, change):
        if form.data["tendered"] == "":
            obj.tendered = 0
        obj.user = request.user
        obj.save()


admin.site.register(Cashdrawer, CashdrawerAdmin)


class VenueAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
        "city",
        "state",
        "country",
        "postalCode",
        "website",
    )


admin.site.register(Venue, VenueAdmin)


class PrettyJSONWidget(widgets.Textarea):
    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
            # these lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in value.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 120)
            return value
        except Exception as e:
            logger.warning("Error while formatting JSON: {}".format(e))
            return super(PrettyJSONWidget, self).format_value(value)


def json_highlight_format_value(value):
    doc = json.dumps(value, indent=2, sort_keys=True)
    # Get the Pygments formatter
    formatter = HtmlFormatter(style="default")

    # Highlight the data
    response = highlight(doc, JsonLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)


class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "timestamp", "integration", "processed")
    list_filter = ("event_type", "processed")
    search_fields = ["event_id"]
    readonly_fields = ("processed", "body_highlighted", "headers_highlighted")
    exclude = ("body", "headers")

    def body_highlighted(self, instance):
        return json_highlight_format_value(instance.body)

    body_highlighted.short_description = "Body"

    def headers_highlighted(self, instance):
        return json_highlight_format_value(instance.headers)

    body_highlighted.short_description = "Headers"


admin.site.register(PaymentWebhookNotification, PaymentWebhookAdmin)


class BadgeTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "paperWidth",
        "paperHeight",
        "marginTop",
        "marginBottom",
        "marginLeft",
        "marginRight",
        "landscape",
        "scale"
    )

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "template"),
            }
        ),
        (
            "Paper Setup",
            {
                "fields": (
                    "landscape",
                    "scale",
                    ("paperWidth", "paperHeight"),
                )
            }
        ),
        (
            "Margins And Padding",
            {
                "fields": (
                    ("marginTop", "marginBottom"),
                    ("marginLeft", "marginRight"),
                ),
            }
        ),
    )

admin.site.register(BadgeTemplate, BadgeTemplateAdmin)
