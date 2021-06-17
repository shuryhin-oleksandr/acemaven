from django.contrib import admin

from app.handling.models import ShippingType, ShippingMode, PackagingType, ContainerType, \
    IMOClass, ReleaseType, Carrier, Airline, Currency, Port, ExchangeRate, ClientPlatformSetting, GeneralSetting, \
    AirTrackingSetting, SeaTrackingSetting, LocalFee
from django.utils.translation import ugettext_lazy as _


@admin.register(ClientPlatformSetting)
class ClientPlatformSettingAdmin(admin.ModelAdmin):
    list_display = (
        'number_of_results',
        'hide_carrier_name',
        'number_of_bids',
        'number_of_days',
        'enable_booking_fee_payment',
    )


@admin.register(GeneralSetting)
class GeneralSettingAdmin(admin.ModelAdmin):
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "show_freight_forwarder_name":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in
                                 GeneralSetting.SHOW_FREIGHT_FORWARDER_NAME_CHOICES]

        return super(GeneralSettingAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(AirTrackingSetting)
class AirTrackingSettingAdmin(admin.ModelAdmin):
    pass


@admin.register(SeaTrackingSetting)
class SeaTrackingSettingAdmin(admin.ModelAdmin):
    pass


@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    search_fields = ('code',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    search_fields = ('code',)
    list_display = ('code', 'is_active', 'is_main',)


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    pass


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('title', 'shipping_type', 'scac', 'code', 'prefix',)
    list_filter = ('shipping_type',)


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


@admin.register(ExchangeRate)
class ExchangeRateTypeAdmin(admin.ModelAdmin):
    list_display = ('currency', 'rate', 'spread',)
    fieldsets = (
        (None, {
            'fields': (
                'rate',
                'spread',
                'currency',
            ),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(is_platforms=True)

    def save_model(self, request, obj, form, change):
        obj.is_platforms = True
        obj.save()


class ListTopFilter(admin.filters.ChoicesFieldListFilter):
    template = 'handling/global_fee_change_list_filter.html'


class RelatedListTopFilter(admin.filters.RelatedFieldListFilter):
    template = 'handling/global_fee_change_list_filter.html'
