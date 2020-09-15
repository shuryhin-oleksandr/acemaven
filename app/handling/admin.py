from django.contrib import admin

from app.handling.models import GlobalFee, LocalFee, ShippingType, ShippingMode, PackagingType, ContainerType, \
    IMOClass, ReleaseType, Carrier, Airline, Currency, Port


@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    pass


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    pass


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    pass


@admin.register(ReleaseType)
class ReleaseTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(IMOClass)
class IMOClassAdmin(admin.ModelAdmin):
    pass


@admin.register(ContainerType)
class ContainerTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ShippingMode)
class ShippingModeAdmin(admin.ModelAdmin):
    list_display = ('title', 'shipping_type',)


@admin.register(ShippingType)
class ShippingTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(GlobalFee)
class GlobalFeeAdmin(admin.ModelAdmin):
    list_display = ('title', 'fee_type', 'value', 'value_type', 'shipping_mode', 'is_active',)


@admin.register(LocalFee)
class LocalFeeAdmin(admin.ModelAdmin):
    list_display = ('title', 'fee_type', 'value', 'value_type', 'shipping_mode', 'company', 'is_active',)
    search_fields = ('company', 'fee_type',)
    list_filter = ('company', 'fee_type',)
