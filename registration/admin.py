from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(HoldType)
admin.site.register(ShirtSizes)
admin.site.register(Event)

admin.site.register(Attendee)


admin.site.register(PriceLevel)
admin.site.register(PriceLevelOption)
