from datetime import date
import copy

from django import forms
from django.contrib import admin
from django.db.models import Max
from django.utils.html import format_html, urlencode
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse

from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from nested_inline.admin import NestedTabularInline, NestedModelAdmin

from .models import *
from .emails import *
import views
import printing

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Event)
admin.site.register(TableSize)

class BanListAdmin(admin.ModelAdmin):
    list_display = ('firstName', 'lastName', 'email')

admin.site.register(BanList, BanListAdmin)

def send_approval_email(modeladmin, request, queryset):
    sendApprovalEmail(queryset)
    queryset.update(emailed=True)
send_approval_email.short_description = "Send approval email and payment instructions"

def send_payment_email(modeladmin, request, queryset):
    for dealer in queryset:
        badge = dealer.getBadge()
        oi = OrderItem.objects.filter(badge=badge).first()
        if oi and oi.order: 
            sendDealerPaymentEmail(dealer,oi.order)
send_payment_email.short_description = "Resend payment confirmation email"

def send_assistant_form_email(modeladmin, request, queryset):
    for dealer in queryset:
        sendDealerAsstFormEmail(dealer)
send_assistant_form_email.short_description = "Send assistent addition form email"


class DealerResource(resources.ModelResource):
    class Meta:
        model = Dealer
        fields = ('id', 'event__name', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email',
                  'businessName', 'approved', 'website', 'description', 'license', 'needPower', 'needWifi',
                  'wallSpace', 'nearTo', 'farFrom', 'tableSize__name', 'reception', 'artShow',
                  'charityRaffle', 'breakfast', 'asstBreakfast', 'willSwitch', 'partners', 'buttonOffer', 'discount',
                  'discountReason', 'emailed')
        export_order = ('id', 'event__name', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email',
                  'businessName', 'approved', 'website', 'description', 'license', 'needPower', 'needWifi',
                  'wallSpace', 'nearTo', 'farFrom', 'tableSize__name', 'reception', 'artShow',
                  'charityRaffle', 'breakfast', 'asstBreakfast', 'willSwitch', 'partners', 'buttonOffer', 'discount',
                  'discountReason', 'emailed')

class DealerAdmin(ImportExportModelAdmin):
    list_display = ('attendee', 'businessName', 'tableSize', 'chairs', 'tables', 'needWifi', 'approved', 'tableNumber', 'emailed', 'paidTotal', 'event')
    list_filter = ('event',)
    save_on_top = True
    resource_class = DealerResource
    actions = [send_approval_email, send_assistant_form_email, send_payment_email]
    readonly_fields = ['get_email']
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('attendee', 'approved'),
                'get_email',
                ('registrationToken', 'event'), 'tableNumber',
                ('discount','discountReason'), 'notes'
            )}
        ),
        (
            'Business Info', 
            {'fields': (
                'businessName', 'license', 'website', 'description'
            )}
        ),
        (
            'Table Request', 
            {'fields':(
                'tableSize', 
                ('willSwitch', 'needPower', 'needWifi', 'wallSpace', 'reception', 'breakfast'),
                ('nearTo', 'farFrom'),
                ('tables', 'chairs'), 'asstBreakfast', 'partners'
            )}
        ),
        (
            'Contributions', 
            {'fields':(
                'artShow', 'buttonOffer', 'charityRaffle'
            )}
        )
    )
    
    def get_email(self, obj):
        return obj.attendee.email
    get_email.short_description = "Attendee Email"


admin.site.register(Dealer, DealerAdmin)

########################################################
#   Staff Admin

def send_staff_registration_email(modeladmin, request, queryset):
    for staff in queryset:
        sendStaffPromotionEmail(staff)
send_staff_registration_email.short_description = "Send registration instructions"

class StaffResource(resources.ModelResource):
    class Meta:
        model = Staff
        fields = ('id', 'event__name', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email',
                  'department__name', 'supervisor', 'title', 'twitter', 'telegram', 'shirtsize__name', 
                  'specialSkills', 'specialFood', 'specialMedical', 'contactName', 'contactPhone', 
                  'contactRelation'
                  )
        export_order = ('id', 'event__name', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email',
                  'department__name', 'supervisor', 'title', 'twitter', 'telegram', 'shirtsize__name', 
                  'specialSkills', 'specialFood', 'specialMedical', 'contactName', 'contactPhone', 
                  'contactRelation'
                  )

class StaffAdmin(ImportExportModelAdmin):
    save_on_top = True
    actions = [send_staff_registration_email, 'copy_to_event']
    list_display = ('attendee', 'get_badge', 'get_email', 'title', 'department', 'shirtsize', 'staff_total', 'event')
    list_filter = ('event','department')
    search_fields = ['attendee__email', 'attendee__lastName', 'attendee__firstName'] 
    resource_class = StaffResource
    readonly_fields = ['get_email', 'get_badge']
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('attendee', 'registrationToken'), 
                ('event', 'get_email', 'get_badge'),
                ('title', 'timesheetAccess'),
                ('department', 'supervisor'),
                ('twitter','telegram'),
                'shirtsize', 
            )}
        ),
        (
            'Emergency Contact', 
            {'fields': (
                'contactName', 'contactPhone', 'contactRelation'
            )}
        ),
        (
            'Misc', 
            {'fields': (
                'specialSkills', 'specialFood', 'specialMedical',
                'notes'
            )}
        ),
    )

    def get_email(self, obj):
        return obj.attendee.email
    get_email.short_description = "Email"

    def get_badge(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge == None: 
            return "--"
        return badge.badgeName
    get_badge.short_description = "Badge Name"

    def staff_total(self, obj):
        badge = Badge.objects.filter(attendee=obj.attendee, event=obj.event).last()
        if badge == None:
            return "--"
        return badge.paidTotal()

    class CopyToEvent(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        event = forms.ModelChoiceField(Event.objects)

    def copy_to_event(self, request, queryset):
        form = None

        if 'event' in request.POST:
            form = self.CopyToEvent(request.POST)

            if form.is_valid():
                event = form.cleaned_data['event']
                count = 0

                for staff in queryset:
                    staff_copy = copy.copy(staff);
                    staff_copy.id = None
                    staff_copy.attendee = staff.attendee
                    staff_copy.event = event
                    staff_copy.registrationToken = getRegistrationToken()
                    staff_copy.save()
                    count += 1

                self.message_user(request, "Successfully copied %d staff to %s." % (count, event))
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.CopyToEvent(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

        return render(request, 'admin/copy_event.html', {'staff': queryset, 'form': form })
    copy_to_event.short_description = "Copy to Event..."


admin.site.register(Staff, StaffAdmin)


########################################################
#   Attendee/Badge Admin

def make_staff(modeladmin, request, queryset):
    event = Event.objects.last()
    for att in queryset:
        staff = Staff(attendee=att,event=event)
        staff.save()
make_staff.short_description = "Add to Staff"

def assign_badge_numbers(modeladmin, request, queryset):
    nonstaff = Attendee.objects.filter(staff=None)
    firstBadge = queryset[0]
    badges = Badge.objects.filter(attendee__in=nonstaff, event=firstBadge.event)
    highest = badges.aggregate(Max('badgeNumber'))['badgeNumber__max']
    for badge in queryset.order_by('registeredDate'): 
        if badge.badgeNumber: continue
        if badge.effectiveLevel() == None: continue
        highest = highest + 1
        badge.badgeNumber = highest 
        badge.save()
assign_badge_numbers.short_description = "Assign badge number"
    
def assign_numbers_and_print(modeladmin, request, queryset):
    nonstaff = Attendee.objects.filter(staff=None)
    firstBadge = queryset[0]
    badges = Badge.objects.filter(attendee__in=nonstaff, event=firstBadge.event)
    highest = badges.aggregate(Max('badgeNumber'))['badgeNumber__max']

    for badge in queryset.order_by('registeredDate'): 
        if badge.badgeNumber: continue
        if badge.effectiveLevel() == None: continue
        highest = highest + 1
        badge.badgeNumber = highest 
        badge.save()

    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        #print the badge
        if badge.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = '{:04}'.format(badge.badgeNumber)
        tags.append({ 
            'name'   : badge.badgeName,
            'number' : badgeNumber,
            'level'  : str(badge.effectiveLevel()),
            'title'  : ''
        })
        badge.printed = True
        badge.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    response = HttpResponseRedirect(reverse(views.printNametag))
    url_params = {
        'file' : pdf_path,
        'next' : request.get_full_path()
    }
    response['Location'] += '?{}'.format(urlencode(url_params))
    return response

assign_numbers_and_print.short_description = "Assign Number and Print"


def print_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        #print the badge
        if badge.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = '{:04}'.format(badge.badgeNumber)
        tags.append({ 
            'name'   : badge.badgeName,
            'number' : badgeNumber,
            'level'  : str(badge.effectiveLevel()),
            'title'  : ''
        })
        badge.printed = True
        badge.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    response = HttpResponseRedirect(reverse(views.printNametag))
    url_params = {
        'file' : pdf_path,
        'next' : request.get_full_path()
    }
    response['Location'] += '?{}'.format(urlencode(url_params))
    return response
print_badges.short_description = "Print Badges"

def print_dealerasst_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        #print the badge
        if badge.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = 'S{:03}'.format(badge.badgeNumber)
        tags.append({ 
            'name'   : badge.badgeName,
            'number' : '',
            'level'  : '',
            'title'  : ''
        })
        badge.printed = True
        badge.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    response = HttpResponseRedirect(reverse(views.printNametag))
    url_params = {
        'file' : pdf_path,
        'next' : request.get_full_path()
    }
    response['Location'] += '?{}'.format(urlencode(url_params))
    return response
print_dealerasst_badges.short_description = "Print Dealer Assistant Badges"


def print_dealer_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        #print the badge
        if badge.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = 'S{:03}'.format(att.badgeNumber)
        tags.append({ 
            'name'   : att.badgeName,
            'number' : '',
            'level'  : '',
            'title'  : ''
        })
        badge.printed = True
        badge.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    response = HttpResponseRedirect(reverse(views.printNametag))
    url_params = {
        'file' : pdf_path,
        'next' : request.get_full_path()
    }
    response['Location'] += '?{}'.format(urlencode(url_params))
    return response
print_dealer_badges.short_description = "Print Dealer Badges"

def assign_staff_badge_numbers(modeladmin, request, queryset):
    staff = Attendee.objects.exclude(staff=None)
    event = staff[0].event
    badges = Badge.objects.filter(attendee__in=staff,event=event)
    highest = badges.aggregate(Max('badgeNumber'))['badgeNumber__max']
    for badge in queryset.order_by('registeredDate'): 
        if badge.badgeNumber: continue
        if badge.effectiveLevel() == None: continue
        highest = highest + 1
        badge.badgeNumber = highest 
        badge.save()
assign_staff_badge_numbers.short_description = "Assign staff badge numbers"

def print_staff_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for badge in queryset:
        #print the badge
        if badge.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = 'S{:03}'.format(badge.badgeNumber)
        staff = badge.attendee.staff
        tags.append({ 
            'name'   : badge.badgeName,
            'number' : badgeNumber,
            'level'  : staff.title,
            'title'  : ''
        })
        badge.printed = True
        badge.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    response = HttpResponseRedirect(reverse(views.printNametag))
    url_params = {
        'file' : pdf_path,
        'next' : request.get_full_path()
    }
    response['Location'] += '?{}'.format(urlencode(url_params))
    return response
print_staff_badges.short_description = "Print Staff Badges"


class AttendeeOptionInline(NestedTabularInline):
    model=AttendeeOptions
    extra=0

class OrderItemInline(NestedTabularInline):
    model=OrderItem
    extra=0
    inlines = [AttendeeOptionInline]
    list_display = ['priceLevel', 'enteredBy']

class BadgeInline(NestedTabularInline):
    model=Badge
    extra=0
    inlines = [OrderItemInline]
    list_display = ['event', 'badgeName', 'badgeNumber', 'registrationToken', 'registrationDate']
    readonly_fields = ['get_age_range', ]

    def get_age_range(self, obj):
        born = obj.attendee.birthdate
        today = date.today()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if age >= 18: return format_html('<span>18+</span>')
        return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')
    get_age_range.short_description = "Age Group"

class BadgeResource(resources.ModelResource):
    badge_level = fields.Field()

    def dehydrate_badge_level(self, badge):
        return badge.effectiveLevel()

    class Meta:
        model = Badge
        fields = ('id', 'event__name', 'badge_level', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email', 'badgeName', 'badgeNumber', 'attendee__aslRequest'
                  )
        export_order = ('id', 'event__name', 'badge_level', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email', 'badgeName', 'badgeNumber', 'attendee__aslRequest'
                  )

class BadgeAdmin(NestedModelAdmin, ImportExportModelAdmin):
    inlines = [OrderItemInline]
    resource_class = BadgeResource
    save_on_top = True
    list_filter = ('event', 'printed')
    list_display = ('attendee', 'badgeName', 'badgeNumber', 'printed', 'paidTotal', 'effectiveLevel', 'abandoned', 'get_age_range')
    search_fields = ['attendee__email', 'attendee__lastName', 'attendee__firstName', 'badgeName', 'badgeNumber'] 
    readonly_fields = ['get_age_range', ]
    actions = [assign_badge_numbers, print_badges, print_dealerasst_badges, assign_numbers_and_print, 
               print_dealer_badges, assign_staff_badge_numbers, print_staff_badges]
    fieldsets = (
        (
	    None, 
            {'fields':(
                'printed',
                ('badgeName', 'badgeNumber', 'get_age_range'),
                ('registeredDate', 'event'), 
                'attendee', 
            )}
        ),
    )

    def get_age_range(self, obj):
        born = obj.attendee.birthdate
        today = date.today()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if age >= 18: return format_html('<span>18+</span>')
        return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')
    get_age_range.short_description = "Age Group"

admin.site.register(Badge, BadgeAdmin)

class AttendeeAdmin(NestedModelAdmin):
    inlines = [BadgeInline]
    save_on_top = True
    actions = [make_staff]
    search_fields = ['email', 'lastName', 'firstName'] 
    list_display = ('firstName', 'lastName',  'email', 'get_age_range')
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('firstName', 'lastName'), 
                ('address1', 'address2'),
                ('city', 'state', 'postalCode', 'country'),
                ('email','phone', 'emailsOk', 'surveyOk'),
                'birthdate',
            )}
        ),
        (
            'Other Con Info', 
            {'fields': (
                'aslRequest', 'volunteerDepts', 'holdType', 'notes'
            )}
        ),
        (
            'Parent Info', 
            {'fields': (
                'parentFirstName', 'parentLastName', 
                'parentPhone', 'parentEmail',
            )}
        ),
    )

    def get_age_range(self, obj):
        born = obj.birthdate
        today = date.today()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if age >= 18: return format_html('<span>18+</span>')
        return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')
    get_age_range.short_description = "Age Group"



admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(AttendeeOptions)

admin.site.register(OrderItem)

class OrderAdmin(NestedModelAdmin):
    list_display = ('reference', 'createdDate', 'total', 'orgDonation', 'charityDonation', 'discount', 'status')
    save_on_top = True
    inlines = [OrderItemInline]
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('total', 'billingType'), 
                ('reference', 'status'), 
                ('discount', 'lastFour'), 
                ('orgDonation', 'charityDonation')
            )}
        ),
        (
            'Billing Address', 
            {'fields': (
                'billingName', 'billingEmail', 'billingAddress1', 'billingAddress2',
                'billingCity', 'billingState', 'billingPostal'
            ), 'classes': ('collapse',)}
        ),
        (
            'Notes', 
            {'fields': (
                'notes',
            ), 'classes': ('collapse',)}
        ),
    )


admin.site.register(Order, OrderAdmin)

class PriceLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'basePrice', 'startDate', 'endDate', 'public', 'group')

admin.site.register(PriceLevel, PriceLevelAdmin)

class PriceLevelOptionAdmin(admin.ModelAdmin):
    list_display = ('optionName', 'optionPrice', 'optionExtraType', 'required', 'active')

admin.site.register(PriceLevelOption, PriceLevelOptionAdmin)

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('codeName', 'amountOff', 'percentOff', 'oneTime', 'used')
    save_on_top = True

admin.site.register(Discount, DiscountAdmin)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'volunteerListOk')

admin.site.register(Department, DepartmentAdmin)
