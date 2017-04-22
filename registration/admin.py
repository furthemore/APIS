from datetime import date

from django.contrib import admin
from django.db.models import Max
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from import_export import resources
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

class JerseyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'number', 'shirtSize')
class StaffJerseyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'number', 'shirtSize')

admin.site.register(Jersey, JerseyAdmin)
admin.site.register(StaffJersey, StaffJerseyAdmin)

admin.site.register(TableSize)


def send_approval_email(modeladmin, request, queryset):
    sendApprovalEmail(queryset)
    queryset.update(emailed=True)
send_approval_email.short_description = "Send approval email and payment instructions"

def send_payment_email(modeladmin, request, queryset):
    for dealer in queryset:
        oi = OrderItem.objects.filter(attendee=dealer.attendee).first()
        if oi and oi.order: 
            sendDealerPaymentEmail(dealer,oi.order)
send_payment_email.short_description = "Resend payment confirmation email"

def send_assistant_form_email(modeladmin, request, queryset):
    for dealer in queryset:
        sendDealerAsstFormEmail(dealer)
send_assistant_form_email.short_description = "Send assistent addition form email"

def print_dealer_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for dealer in queryset:
        #print the badge
        att = dealer.attendee
        if att.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = 'S{:03}'.format(att.badgeNumber)
        tags.append({ 
            'name'   : att.badgeName,
            'number' : '',
            'level'  : '',
            'title'  : ''
        })
        att.printed = True
        att.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    # FIXME: get site URL from sites contrib package?
    response = HttpResponseRedirect(reverse(views.printNametag))
    response['Location'] += '?file={}'.format(pdf_path)
    return response
print_dealer_badges.short_description = "Print Dealer Badges"


class DealerResource(resources.ModelResource):
    class Meta:
        model = Dealer
        fields = ('id', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email', 'attendee__badgeName',
                  'businessName', 'approved', 'website', 'description', 'license', 'needPower', 'needWifi',
                  'wallSpace', 'nearTo', 'farFrom', 'tableSize__name', 'reception', 'artShow',
                  'charityRaffle', 'breakfast', 'willSwitch', 'partners', 'buttonOffer', 'discount',
                  'discountReason', 'emailed')
        export_order = ('id', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email', 'attendee__badgeName',
                  'businessName', 'approved', 'website', 'description', 'license', 'needPower', 'needWifi',
                  'wallSpace', 'nearTo', 'farFrom', 'tableSize__name', 'reception', 'artShow',
                  'charityRaffle', 'breakfast', 'willSwitch', 'partners', 'buttonOffer', 'discount',
                  'discountReason', 'emailed')

class DealerAdmin(ImportExportModelAdmin):
    list_display = ('attendee', 'businessName', 'tableSize', 'chairs', 'tables', 'needWifi', 'approved', 'tableNumber', 'emailed', 'paidTotal')
    save_on_top = True
    resource_class = DealerResource
    actions = [send_approval_email, send_assistant_form_email, send_payment_email, print_dealer_badges]
    readonly_fields = ['get_email']
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('attendee', 'approved'), 
                'get_email',
                'registrationToken', 'tableNumber',
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
                ('tables', 'chairs'), 'partners'
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

def assign_staff_badge_numbers(modeladmin, request, queryset):
    highest = Staff.objects.all().aggregate(Max('attendee__badgeNumber'))['attendee__badgeNumber__max']
    for staff in queryset.order_by('attendee__registeredDate'): 
        if staff.attendee.badgeNumber: continue
        if staff.attendee.effectiveLevel() == None: continue
        highest = highest + 1
        a = staff.attendee
        a.badgeNumber = highest 
        a.save()
assign_staff_badge_numbers.short_description = "Assign staff badge numbers"

def print_staff_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for staff in queryset:
        #print the badge
        att = staff.attendee
        if att.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = 'S{:03}'.format(att.badgeNumber)
        tags.append({ 
            'name'   : att.badgeName,
            'number' : badgeNumber,
            'level'  : staff.title,
            'title'  : ''
        })
        att.printed = True
        att.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    # FIXME: get site URL from sites contrib package?
    response = HttpResponseRedirect(reverse(views.printNametag))
    response['Location'] += '?file={}'.format(pdf_path)
    return response
print_staff_badges.short_description = "Print Staff Badges"


class StaffResource(resources.ModelResource):
    class Meta:
        model = Staff
        fields = ('id','attendee__badgeNumber', 'attendee__printed', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email', 'attendee__badgeName',
                  'department__name', 'supervisor', 'title', 'twitter', 'telegram', 'shirtsize__name', 
                  'specialSkills', 'specialFood', 'specialMedical', 'contactName', 'contactPhone', 
                  'contactRelation'
                  )
        export_order = ('id', 'attendee__badgeNumber', 'attendee__printed', 'attendee__firstName', 'attendee__lastName', 'attendee__address1', 
                  'attendee__address2', 'attendee__city', 'attendee__state', 'attendee__country',
                  'attendee__postalCode', 'attendee__phone', 'attendee__email', 'attendee__badgeName',
                  'department__name', 'supervisor', 'title', 'twitter', 'telegram', 'shirtsize__name', 
                  'specialSkills', 'specialFood', 'specialMedical', 'contactName', 'contactPhone', 
                  'contactRelation'
                  )

class StaffAdmin(ImportExportModelAdmin):
    save_on_top = True
    actions = [send_staff_registration_email, assign_staff_badge_numbers, print_staff_badges]
    list_display = ('attendee', 'get_email', 'get_badge', 'title', 'department', 'shirtsize', 'staff_total')
    list_filter = ('department',)
    search_fields = ['attendee__email', 'attendee__badgeName', 'attendee__lastName', 'attendee__firstName'] 
    resource_class = StaffResource
    readonly_fields = ['get_email', 'get_badge']
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('attendee', 'registrationToken'), 
                ('get_email', 'get_badge'),
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
        return obj.attendee.badgeName
    get_badge.short_description = "Badge Name"

    def staff_total(self, obj):
        return obj.attendee.paidTotal()

admin.site.register(Staff, StaffAdmin)


########################################################
#   Attendee Admin

def make_staff(modeladmin, request, queryset):
    for att in queryset:
        staff = Staff(attendee=att)
        staff.save()
make_staff.short_description = "Add to Staff"

def clear_abandons(modeladmin, request, queryset):
    for att in queryset:
        if att.abandoned() == True:
           jerseyTypes = PriceLevelOption.objects.filter(optionExtraType='Jersey')
           orderItems = OrderItem.objects.filter(attendee=att)
           jerseyOptions = AttendeeOptions.objects.filter(option__in=jerseyTypes, orderItem__in=orderItems)
           for jerOpt in jerseyOptions:
             jersey = Jersey.objects.get(id=jerOpt.optionValue)
             jersey.delete()
           att.delete()
clear_abandons.short_description = "***Delete Abandoned Orders***"

def assign_badge_numbers(modeladmin, request, queryset):
    nonstaff = Attendee.objects.filter(staff=None)
    highest = nonstaff.aggregate(Max('badgeNumber'))['badgeNumber__max']
    for att in queryset.order_by('registeredDate'): 
        if att.badgeNumber: continue
        if att.effectiveLevel() == None: continue
        highest = highest + 1
        att.badgeNumber = highest 
        att.save()
assign_badge_numbers.short_description = "Assign badge numbers"

def print_badges(modeladmin, request, queryset):
    con = printing.Main(local=True)
    tags = []
    for att in queryset:
        #print the badge
        if att.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = '{:04}'.format(att.badgeNumber)
        tags.append({ 
            'name'   : att.badgeName,
            'number' : badgeNumber,
            'level'  : str(att.effectiveLevel()),
            'title'  : ''
        })
        att.printed = True
        att.save()
    con.nametags(tags, theme='apis')
    # serve up this file
    pdf_path = con.pdf.split('/')[-1]
    # FIXME: get site URL from sites contrib package?
    response = HttpResponseRedirect(reverse(views.printNametag))
    response['Location'] += '?file={}'.format(pdf_path)
    return response
print_badges.short_description = "Print Badges"


class AttendeeOptionInline(NestedTabularInline):
    model=AttendeeOptions
    extra=1

class OrderItemInline(NestedTabularInline):
    model=OrderItem
    extra=0
    inlines = [AttendeeOptionInline]
    list_display = ['attendee', 'priceLevel', 'get_age_range', 'enteredBy']
    readonly_fields = ['get_age_range', ]

    def get_age_range(self, obj):
        born = obj.attendee.birthdate
        today = date.today()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if age >= 18: return format_html('<span>18+</span>')
        return format_html('<span style="color:red">MINOR FORM<br/>REQUIRED</span>')
    get_age_range.short_description = "Age Group"


class AttendeeAdmin(NestedModelAdmin):
    inlines = [OrderItemInline]
    save_on_top = True
    actions = [make_staff, clear_abandons, assign_badge_numbers, print_badges]
    search_fields = ['email', 'badgeName', 'lastName', 'firstName'] 
    list_filter = ('event',)
    list_display = ('firstName', 'lastName', 'badgeName', 'email', 'paidTotal', 'effectiveLevel', 'abandoned', 'registeredDate')
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('firstName', 'lastName'), 
                ('registrationToken', 'event'), 
                ('badgeName', 'badgeNumber', 'printed'),
                ('address1', 'address2'),
                ('city', 'state', 'postalCode', 'country'),
                ('email','phone', 'emailsOk'),
                'birthdate', 'registeredDate',
            )}
        ),
        (
            'Other Con Info', 
            {'fields': (
                'volunteerDepts', 'holdType', 'notes'
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


admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(AttendeeOptions)

class AttendeeOnsite(Attendee):
    class Meta:
        proxy=True
        verbose_name='Attendee Onsite 2017'
        verbose_name_plural='Attendee Onsite 2017'

class AttendeeOnsiteAdmin(NestedModelAdmin):
    inlines = [OrderItemInline]
    save_on_top = True
    actions = [assign_badge_numbers, print_badges]
    search_fields = ['email', 'badgeName', 'lastName', 'firstName'] 
    list_display = ('firstName', 'lastName', 'badgeName', 'effectiveLevel', 'is_minor', 'badgeNumber', 'printed')
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('firstName', 'lastName'), 
                ('badgeName', 'badgeNumber'),
                ('address1', 'address2'),
                ('city', 'state', 'postalCode', 'country'),
                ('email','phone', 'emailsOk'),
                'birthdate',
            )}
        ),
        (
            'Parent Info', 
            {'fields': (
                'parentFirstName', 'parentLastName', 
                'parentPhone', 'parentEmail',
            ),  'classes': ('collapse',)}
        ),
        (
            'Other Con Info', 
            {'fields': (
                'holdType',
            ),  'classes': ('collapse',)}
        ),
    )

    def is_minor(self, obj):
        today = date.today()
        born = obj.birthdate
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if age >= 18: return ""
        return format_html('<span style="color:red">YES</span>')

    def get_actions(self, request):
        actions = super(AttendeeOnsiteAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        ev = Event.objects.get(name='Furthemore 2017')
        return super(AttendeeOnsiteAdmin,self).get_queryset(request).filter(event=ev).filter(printed=False)

admin.site.register(AttendeeOnsite, AttendeeOnsiteAdmin)

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
    list_display = ('optionName', 'priceLevel', 'optionPrice', 'optionExtraType', 'required')

admin.site.register(PriceLevelOption, PriceLevelOptionAdmin)

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('codeName', 'amountOff', 'percentOff', 'oneTime', 'used')
    save_on_top = True

admin.site.register(Discount, DiscountAdmin)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'volunteerListOk')

admin.site.register(Department, DepartmentAdmin)
