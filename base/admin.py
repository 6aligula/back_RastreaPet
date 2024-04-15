from django.contrib import admin
from .models import *

class PetImageInline(admin.StackedInline):
    model = PetImage
    extra = 1

class PetAdmin(admin.ModelAdmin):
    inlines = [PetImageInline, ]

admin.site.register(Pet, PetAdmin)
admin.site.register(Trail)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
