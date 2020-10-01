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
    list_display = ('title', 'shipping_type', )


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


class ListTopFilter(admin.filters.ChoicesFieldListFilter):
    template = 'handling/global_fee_change_list_filter.html'


class RelatedListTopFilter(admin.filters.RelatedFieldListFilter):
    template = 'handling/global_fee_change_list_filter.html'


@admin.register(GlobalFee)
class GlobalFeeAdmin(admin.ModelAdmin):
    change_list_template = 'handling/global_fee_change_list.html'
    list_display = ('shipping_mode', 'value_type', 'value', 'is_active', )
    radio_fields = {'value_type': admin.VERTICAL}
    list_editable = ('value', 'value_type', 'is_active',)
    list_filter = (
        ('fee_type', ListTopFilter),
    )
    ordering = ('-shipping_mode', )


@admin.register(LocalFee)
class LocalFeeAdmin(admin.ModelAdmin):
    change_list_template = 'handling/global_fee_change_list.html'
    list_display = ('fee_type', 'value', 'value_type', 'shipping_mode', 'company', 'is_active',)
    search_fields = ('company__name', 'fee_type',)
    list_filter = (
        ('company', RelatedListTopFilter, ),
        ('fee_type', ListTopFilter, ),
    )
