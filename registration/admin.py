from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import *

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Event)
admin.site.register(Jersey)
admin.site.register(TableSize)


class DealerResource(resources.ModelResource):
    class Meta:
        model = Dealer

class DealerAdmin(ImportExportModelAdmin):
    list_display = ('attendee', 'businessName', 'tableSize', 'chairs', 'tables', 'needWifi', 'approved', 'tableNumber')
    resource_class = DealerResource

admin.site.register(Dealer, DealerAdmin)



admin.site.register(Attendee)
admin.site.register(AttendeeOptions)
admin.site.register(OrderItem)
admin.site.register(Order)

admin.site.register(PriceLevel)
admin.site.register(PriceLevelOption)

admin.site.register(Department)
