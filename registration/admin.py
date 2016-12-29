from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import *
from .emails import *

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Event)
admin.site.register(Jersey)
admin.site.register(TableSize)


def send_approval_email(modeladmin, request, queryset):
    sendApprovalEmail(queryset)
    queryset.update(emailed=True)
send_approval_email.short_description = "Send approval email and payment instructions"

class DealerResource(resources.ModelResource):
    class Meta:
        model = Dealer

class DealerAdmin(ImportExportModelAdmin):
    list_display = ('attendee', 'businessName', 'tableSize', 'chairs', 'tables', 'needWifi', 'approved', 'tableNumber', 'paid', 'emailed')
    save_on_top = True
    resource_class = DealerResource
    actions = [send_approval_email]
    fieldsets = (
        (
	    None, 
            {'fields':(
                ('attendee', 'approved'), 
                'registrationToken', 'tableNumber',
                ('discount','discountReason'), 'notes'
            )}
        ),
        (
            'Business Info', 
            {'fields': (
                'businessName', 'license', 'website', 'description', 'partners'
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
                'buttonOffer', 'charityRaffle'
            )}
        )
    )

admin.site.register(Dealer, DealerAdmin)


class StaffAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('attendee', 'department')

admin.site.register(Staff, StaffAdmin)

def make_staff(modeladmin, request, queryset):
    for att in queryset:
        staff = Staff(attendee=att)
        staff.save()
        #todo: send staff reg link
send_approval_email.short_description = "Add to Staff"

class AttendeeAdmin(admin.ModelAdmin):
    save_on_top = True
    actions = [make_staff]

admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(AttendeeOptions)
admin.site.register(OrderItem)
admin.site.register(Order)

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

admin.site.register(Department)
