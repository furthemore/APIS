import cgi
import copy
from datetime import date

import printing
import views
from django import forms
from django.conf.urls import url
from django.contrib import admin, auth, messages
from django.contrib.admin.models import DELETION, LogEntry
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import escape, format_html, urlencode
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from nested_inline.admin import NestedModelAdmin, NestedTabularInline

import registration.emails
import registration.views.printing

from .models import *

TWOPLACES = Decimal(10) ** -2

admin.site.site_url = None
admin.site.site_header = "APIS Backoffice"

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Event)
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


admin.site.register(Firebase, FirebaseAdmin)


class BanListAdmin(admin.ModelAdmin):
    list_display = ("firstName", "lastName", "email", "reason")


admin.site.register(BanList, BanListAdmin)


def send_staff_token_email(modeladmin, request, queryset):
    for token in queryset:
        sendNewStaffEmail(token)
        token.sent = True
        token.save()


send_staff_token_email.short_description = "Send New Staff registration email"


class TempTokenAdmin(admin.ModelAdmin):
    actions = [send_staff_token_email]
    list_display = ["email", "token", "sent", "used"]


admin.site.register(TempToken, TempTokenAdmin)


def send_approval_email(modeladmin, request, queryset):
    sendApprovalEmail(queryset)
    queryset.update(emailed=True)


send_approval_email.short_description = "Send approval email and payment instructions"


def mark_as_approved(modeladmin, request, queryset):
    for dealer in queryset:
        dealer.approved = True
        dealer.save()


mark_as_approved.short_description = "Approve selected dealers"


def send_payment_email(modeladmin, request, queryset):
    for dealer in queryset:
        badge = dealer.getBadge()
        oi = OrderItem.objects.filter(badge=badge).first()
        if oi and oi.order:
            sendDealerPaymentEmail(dealer, oi.order)


send_payment_email.short_description = "Resend payment confirmation email"


def send_assistant_form_email(modeladmin, request, queryset):
    for dealer in queryset:
        sendDealerAsstFormEmail(dealer)


send_assistant_form_email.short_description = "Send assistent addition form email"


class DealerAsstInline(NestedTabularInline):
    model = DealerAsst
    extra = 0


class DealerAsstResource(resources.ModelResource):
    class Meta:
        model = DealerAsst
        fields = (
            "id",
            "name",
            "email",
            "license",
            "event__name",
            "dealer__businessName",
            "dealer__attendee__email",
            "dealer__approved",
            "dealer__tableNumber",
        )


class DealerAsstAdmin(ImportExportModelAdmin):
    save_on_top = True
    list_display = (
        "name",
        "email",
        "license",
        "event",
        "dealer_businessname",
        "dealer_approved",
    )
    list_filter = ("event", "dealer__approved")
    search_fields = ["name", "email"]
    readonly_fields = ["dealer_businessname", "dealer_approved"]
    resource_class = DealerAsstResource

    def dealer_businessname(self, obj):
        return obj.dealer.businessName

    def dealer_approved(self, obj):
        return obj.dealer.approved


admin.site.register(DealerAsst, DealerAsstAdmin)


class DealerResource(resources.ModelResource):
    class Meta:
        model = Dealer
        fields = (
            "id",
            "event__name",
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
    save_on_top = True
    inlines = [DealerAsstInline]
    resource_class = DealerResource
    actions = [
        mark_as_approved,
        send_approval_email,
        send_assistant_form_email,
        send_payment_email,
    ]
    readonly_fields = ["get_email"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("attendee", "approved"),
                    "get_email",
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


admin.site.register(Dealer, DealerAdmin)


########################################################
#   Staff Admin


def checkin_staff(modeladmin, request, queryset):
    for staff in queryset:
        staff.checkedIn = True
        staff.save()


checkin_staff.short_description = "Check in staff"


def send_staff_registration_email(modeladmin, request, queryset):
    for staff in queryset:
        sendStaffPromotionEmail(staff)


send_staff_registration_email.short_description = "Send registration instructions"


class StaffResource(resources.ModelResource):
    class Meta:
        model = Staff
        fields = (
            "id",
            "event__name",
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


class StaffAdmin(ImportExportModelAdmin):
    save_on_top = True
    actions = [send_staff_registration_email, checkin_staff, "copy_to_event"]
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
    search_fields = ["attendee__email", "attendee__lastName", "attendee__firstName"]
    resource_class = StaffResource
    readonly_fields = ["get_email", "get_badge", "get_badge_id"]
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
                    staff_copy = copy.copy(staff)
                    staff_copy.id = None
                    staff_copy.attendee = staff.attendee
                    staff_copy.event = event
                    staff_copy.registrationToken = getRegistrationToken()
                    staff_copy.save()
                    count += 1

                self.message_user(
                    request, "Successfully copied %d staff to %s." % (count, event)
                )
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.CopyToEvent(
                initial={
                    "_selected_action": request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
                }
            )

        return render(
            request, "admin/copy_event.html", {"staff": queryset, "form": form}
        )

    copy_to_event.short_description = "Copy to Event..."


admin.site.register(Staff, StaffAdmin)


########################################################
#   Attendee/Badge Admin


def make_staff(modeladmin, request, queryset):
    event = Event.objects.last()
    for att in queryset:
        staff = Staff(attendee=att, event=event)
        staff.save()


make_staff.short_description = "Add to Staff"


def send_upgrade_form_email(modeladmin, request, queryset):
    for badge in queryset:
        registration.emails.send_upgrade_instructions(badge)


send_upgrade_form_email.short_description = "Send upgrade info email"


def assign_badge_numbers(modeladmin, request, queryset):
    nonstaff = Attendee.objects.filter(staff=None)
    firstBadge = queryset[0]
    badges = Badge.objects.filter(attendee__in=nonstaff, event=firstBadge.event)
    highest = badges.aggregate(Max("badgeNumber"))["badgeNumber__max"]
    for badge in queryset.order_by("registeredDate"):
        if badge.badgeNumber:
            continue
        if badge.effectiveLevel() is None:
            continue
        highest = highest + 1
        badge.badgeNumber = highest
        badge.save()


assign_badge_numbers.short_description = "Assign badge number"


def assign_numbers_and_print(modeladmin, request, queryset):
    nonstaff = Attendee.objects.filter(staff=None)
    firstBadge = queryset[0]
    badges = Badge.objects.filter(attendee__in=nonstaff, event=firstBadge.event)
    highest = badges.aggregate(Max("badgeNumber"))["badgeNumber__max"]

    for badge in queryset.order_by("registeredDate"):
        if badge.badgeNumber:
            continue
        if badge.effectiveLevel() is None:
            continue
        highest = highest + 1
        badge.badgeNumber = highest
        badge.save()

    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "{:04}".format(badge.badgeNumber)
        tags.append(
            {
                "name": cgi.escape(badge.badgeName),
                "number": badgeNumber,
                "level": cgi.escape(str(badge.effectiveLevel())),
                "title": "",
                "age": get_attendee_age(badge.attendee),
            }
        )
        badge.printed = True
        badge.save()
    con.nametags(tags, theme=badge.event.badgeTheme)
    # serve up this file
    pdf_path = con.pdf.split("/")[-1]
    response = HttpResponseRedirect(reverse(registration.views.printing.printNametag))
    url_params = {"file": pdf_path, "next": request.get_full_path()}
    response["Location"] += "?{}".format(urlencode(url_params))
    return response


assign_numbers_and_print.short_description = "Assign Number and Print"


def get_attendee_age(attendee):
    born = attendee.birthdate
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age


def print_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "{:04}".format(badge.badgeNumber)

        # Exclude staff badges
        try:
            staff = Staff.objects.get(attendee=badge.attendee, event=badge.event)
            messages.warning(
                request,
                u"{0} is on staff, so we skipped printing an attendee badge".format(
                    badge.badgeName
                ),
            )
        except Staff.DoesNotExist:
            tags.append(
                {
                    "name": cgi.escape(badge.badgeName),
                    "number": badgeNumber,
                    "level": cgi.escape(str(badge.effectiveLevel())),
                    "title": "",
                    "age": get_attendee_age(badge.attendee),
                }
            )
            badge.printed = True
            badge.save()
    con.nametags(tags, theme=badge.event.badgeTheme)
    # serve up this file
    pdf_path = con.pdf.split("/")[-1]
    response = HttpResponseRedirect(reverse(registration.views.printing.printNametag))
    url_params = {"file": pdf_path, "next": request.get_full_path()}
    response["Location"] += "?{}".format(urlencode(url_params))
    return response


print_badges.short_description = "Print Badges"


def print_label_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "{:04}".format(badge.badgeNumber)

        # Exclude staff badges
        try:
            staff = Staff.objects.get(attendee=badge.attendee, event=badge.event)
            messages.warning(
                request,
                u"{0} is on staff, so we skipped printing an attendee badge".format(
                    badge.badgeName
                ),
            )
        except Staff.DoesNotExist:
            tags.append(
                {
                    "name": cgi.escape(badge.badgeName),
                    "number": badgeNumber,
                    "level": cgi.escape(str(badge.effectiveLevel())),
                    "title": "",
                    "age": get_attendee_age(badge.attendee),
                }
            )
            badge.printed = True
            badge.save()
    con.nametags(tags, theme="fd_labels")
    # serve up this file
    pdf_path = con.pdf.split("/")[-1]
    response = HttpResponseRedirect(reverse(registration.views.printing.printNametag))
    url_params = {"file": pdf_path, "next": request.get_full_path()}
    response["Location"] += "?{}".format(urlencode(url_params))
    return response


print_label_badges.short_description = "Print Label Badges"


def print_dealerasst_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "S{:03}".format(badge.badgeNumber)
        tags.append(
            {
                "name": cgi.escape(badge.badgeName),
                "number": badge.badgeNumber,
                "level": "Dealer",
                "title": "",
                "age": get_attendee_age(badge.attendee),
            }
        )
        badge.printed = True
        badge.save()
    con.nametags(tags, theme=badge.event.badgeTheme)
    # serve up this file
    pdf_path = con.pdf.split("/")[-1]
    response = HttpResponseRedirect(reverse(registration.views.printing.printNametag))
    url_params = {"file": pdf_path, "next": request.get_full_path()}
    response["Location"] += "?{}".format(urlencode(url_params))
    return response


print_dealerasst_badges.short_description = "Print Dealer Assistant Badges"


def print_dealer_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "S{:03}".format(badge.badgeNumber)
        try:
            dealers = Dealer.objects.get(attendee=badge.attendee, event=badge.event)
        except Dealer.DoesNotExist:
            messages.warning(
                request,
                u"{0} is not a dealer, so we skipped printing a dealer badge for them".format(
                    badge.badgeName
                ),
            )
            continue

        tags.append(
            {
                "name": cgi.escape(badge.badgeName),
                "number": badge.badgeNumber,
                "level": "Dealer",
                "title": "",
                "age": get_attendee_age(badge.attendee),
            }
        )
        badge.printed = True
        badge.save()
    if len(tags) > 0:
        con.nametags(tags, theme=badge.event.badgeTheme)
        # serve up this file
        pdf_path = con.pdf.split("/")[-1]
        response = HttpResponseRedirect(
            reverse(registration.views.printing.printNametag)
        )
        url_params = {"file": pdf_path, "next": request.get_full_path()}
        response["Location"] += "?{}".format(urlencode(url_params))
        return response


print_dealer_badges.short_description = "Print Dealer Badges"


def assign_staff_badge_numbers(modeladmin, request, queryset):
    staff = Attendee.objects.exclude(staff=None)
    event = staff[0].event
    badges = Badge.objects.filter(attendee__in=staff, event=event)
    highest = badges.aggregate(Max("badgeNumber"))["badgeNumber__max"]
    for badge in queryset.order_by("registeredDate"):
        if badge.badgeNumber:
            continue
        if badge.effectiveLevel() is None:
            continue
        highest = highest + 1
        badge.badgeNumber = highest
        badge.save()


assign_staff_badge_numbers.short_description = "Assign staff badge numbers"


def print_staff_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        # print the badge
        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "S-{:03}".format(badge.badgeNumber)
        try:
            staff = Staff.objects.get(attendee=badge.attendee, event=badge.event)
        except Staff.DoesNotExist:
            messages.warning(
                request,
                u"{0} is not on staff, so we skipped printing a staff badge for them".format(
                    badge.badgeName
                ),
            )
            continue
        except Staff.MultipleObjectsReturned:
            messages.error(
                request,
                u"{0} was added to staff multiple times! - dedupe and try again.".format(
                    badge.attendee
                ),
            )
            continue

        tags.append(
            {
                "name": cgi.escape(badge.badgeName),
                "number": badgeNumber,
                "level": "Staff",
                "title": cgi.escape(staff.title),
                "age": get_attendee_age(badge.attendee),
            }
        )
        badge.printed = True
        badge.save()
    con.nametags(tags, theme=badge.event.badgeTheme)
    # serve up this file
    pdf_path = con.pdf.split("/")[-1]
    response = HttpResponseRedirect(reverse(registration.views.printing.printNametag))
    url_params = {"file": pdf_path, "next": request.get_full_path()}
    response["Location"] += "?{}".format(urlencode(url_params))
    return response


print_staff_badges.short_description = "Print Staff Badges"


class AttendeeOptionInline(NestedTabularInline):
    model = AttendeeOptions
    extra = 0


class OrderItemInline(NestedTabularInline):
    model = OrderItem
    raw_id_fields = ("badge", "order")
    extra = 0
    inlines = [AttendeeOptionInline]
    list_display = ["priceLevel", "enteredBy"]


class BadgeInline(NestedTabularInline):
    model = Badge
    extra = 0
    inlines = [OrderItemInline]
    list_display = [
        "event",
        "badgeName",
        "badgeNumber",
        "registrationToken",
        "registrationDate",
    ]
    readonly_fields = [
        "get_age_range",
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
    inlines = [OrderItemInline]
    resource_class = BadgeResource
    save_on_top = True
    list_filter = ("event", "printed", PriceLevelFilter)
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
        "badgeName",
        "badgeNumber",
    ]
    readonly_fields = ["get_age_range"]
    actions = [
        assign_badge_numbers,
        print_badges,
        print_label_badges,
        print_dealerasst_badges,
        assign_numbers_and_print,
        print_dealer_badges,
        assign_staff_badge_numbers,
        print_staff_badges,
        send_upgrade_form_email,
        "cull_abandoned_carts",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "printed",
                    ("badgeName", "badgeNumber", "get_age_range"),
                    ("registeredDate", "event"),
                    "attendee",
                )
            },
        ),
    )

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
    search_fields = ["email", "lastName", "firstName"]
    list_display = ("firstName", "lastName", "email", "get_age_range")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("firstName", "lastName"),
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


admin.site.register(OrderItem, OrderItemAdmin)


def send_registration_email(modeladmin, request, queryset):
    for order in queryset:
        registration.emails.sendRegistrationEmail(order, order.billingEmail)


send_registration_email.short_description = "Send registration email"


class OrderAdmin(ImportExportModelAdmin, NestedModelAdmin):
    list_display = (
        "reference",
        "createdDate",
        "total",
        "orgDonation",
        "charityDonation",
        "discount",
        "status",
    )
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

    class RefundForm(forms.Form):
        amount = forms.DecimalField(min_value=0, decimal_places=2)

    def save_model(self, request, obj, form, change):
        if not request.user.has_perm("registration.issue_refund"):
            if form.data["status"] == Order.REFUNDED:
                status = Order.PENDING
                if obj.id:
                    status = Order.objects.get(id=obj.id).status
                messages.add_message(
                    request,
                    messages.ERROR,
                    "You do not have permission to issue refunds. "
                    "The order status has been reverted to {0}".format(status),
                )
                obj.status = status
        obj.save()

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        my_urls = [
            url(r"^(.+)/refund/$", self.refund_view, name="order_refund"),
        ]
        return my_urls + urls

    def refund_view(self, request, order_id, extra_context=None):
        form = None

        order = Order.objects.get(id=order_id)

        if "amount" in request.POST:
            form = self.RefundForm(request.POST)

            if form.is_valid():
                amount = Decimal(form.cleaned_data["amount"]).quantize(TWOPLACES)

                if amount <= 0:
                    messages.error(
                        request,
                        "Refund amount (${0}) cannot be negative or non-zero".format(
                            amount
                        ),
                    )
                elif amount > order.total:
                    messages.error(
                        request,
                        "Refund amount (${0}) cannot exceed order total (${1})".format(
                            amount, order.total
                        ),
                    )
                else:
                    messages.success(request, "refund amount: {0}".format(amount))
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.RefundForm(initial={"amount": order.total,})

        context = {
            "form": form,
            "order": order,
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
    list_display = ("codeName", "amountOff", "percentOff", "oneTime", "used")
    save_on_top = True


admin.site.register(Discount, DiscountAdmin)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "volunteerListOk")


admin.site.register(Department, DepartmentAdmin)


class CashdrawerAdmin(ImportExportModelAdmin):
    list_display = ("timestamp", "action", "total", "tendered", "user")

    def save_model(self, request, obj, form, change):
        if form.data["tendered"] == "":
            obj.tendered = 0
        obj.user = request.user
        obj.save()


admin.site.register(Cashdrawer, CashdrawerAdmin)
