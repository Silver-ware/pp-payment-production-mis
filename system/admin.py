from django.contrib import admin
from .models import Customer, Service, Order, Payment, Inventory, Production, PricingOption, Supplier, PaymentMethod, InventoryCategory
from .models import BusinessDetails, Equipment, SystemSettings, CustomizationOption

admin.site.register(Customer)
admin.site.register(Service)
admin.site.register(CustomizationOption)
admin.site.register(PricingOption)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(PaymentMethod)
admin.site.register(Inventory)
admin.site.register(InventoryCategory)
admin.site.register(Supplier)
admin.site.register(Production)
admin.site.register(BusinessDetails)
admin.site.register(Equipment)
admin.site.register(SystemSettings)

# class PricingOptionInline(admin.TabularInline):
#     model = PricingOption
#     extra = 1

# @admin.register(Service)
# class ServiceAdmin(admin.ModelAdmin):
#     inlines = [PricingOptionInline]

# @admin.register(CustomizationOption)
# class CustomizationOptionAdmin(admin.ModelAdmin):
#     pass

# @admin.register(PricingOption)
# class PricingOptionAdmin(admin.ModelAdmin):
#     list_display = ('service', 'customization_option', 'description', 'price')



