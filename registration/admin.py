from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Event)
admin.site.register(Jersey)
admin.site.register(TableSize)

admin.site.register(Dealer)

admin.site.register(Attendee)
admin.site.register(AttendeeOptions)
admin.site.register(OrderItem)
admin.site.register(Order)

admin.site.register(PriceLevel)
admin.site.register(PriceLevelOption)

admin.site.register(Department)
