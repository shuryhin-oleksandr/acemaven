from django.db.utils import ProgrammingError
from django.utils import timezone

from rest_framework import serializers

from app.handling.models import Carrier, Port, ShippingMode, ShippingType, ContainerType, Currency, PackagingType, \
    ReleaseType, ExchangeRate, BillingExchangeRate
from app.booking.models import AdditionalSurcharge
from app.location.models import Country


try:
    MAIN_COUNTRY_CODE = Country.objects.filter(is_main=True).first().code
except (ProgrammingError, AttributeError):
    MAIN_COUNTRY_CODE = 'BR'


class PackagingTypeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = (
            'id',
            'code',
            'description',
        )


class AdditionalSurchargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalSurcharge
        fields = (
            'id',
            'title',
        )


class ContainerTypesBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerType
        fields = (
            'id',
            'code',
        )


class ContainerTypesSerializer(ContainerTypesBaseSerializer):
    class Meta(ContainerTypesBaseSerializer.Meta):
        model = ContainerType
        fields = ContainerTypesBaseSerializer.Meta.fields + (
            'shipping_mode',
            'is_frozen',
            'can_be_dangerous',
        )


class CarrierBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = (
            'id',
            'title',
        )


class CarrierSerializer(CarrierBaseSerializer):
    class Meta(CarrierBaseSerializer.Meta):
        fields = CarrierBaseSerializer.Meta.fields + (
            'shipping_type',
        )


class PortSerializer(serializers.ModelSerializer):
    is_local = serializers.SerializerMethodField()
    coordinates = serializers.DictField(source='get_lat_long_coordinates')

    class Meta:
        model = Port
        fields = (
            'id',
            'code',
            'name',
            'display_name',
            'is_local',
            'coordinates',
        )

    def get_is_local(self, obj):
        return True if obj.code.startswith(MAIN_COUNTRY_CODE) else False


class ShippingModeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMode
        fields = (
            'id',
            'title',
        )


class ShippingModeSerializer(ShippingModeBaseSerializer):
    container_types = serializers.SerializerMethodField()
    packaging_types = PackagingTypeBaseSerializer(many=True)
    additional_surcharges = AdditionalSurchargeSerializer(many=True)

    class Meta(ShippingModeBaseSerializer.Meta):
        fields = ShippingModeBaseSerializer.Meta.fields + (
            'container_types',
            'packaging_types',
            'additional_surcharges',
            'is_need_volume',
        )

    def get_container_types(self, obj):
        is_freight_rate = self.context.get('request').query_params.get('is_freight_rate')
        queryset = obj.container_types.all()
        data = [] if obj.title == 'ULD' and is_freight_rate else ContainerTypesSerializer(queryset, many=True).data
        return data


class ShippingTypeSerializer(serializers.ModelSerializer):
    shipping_modes = ShippingModeSerializer(many=True)

    class Meta:
        model = ShippingType
        fields = (
            'id',
            'title',
            'shipping_modes',
        )


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = (
            'id',
            'code',
        )


class ReleaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseType
        fields = (
            'id',
            'code',
            'title',
        )


class ExchangeRateBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = (
            'id',
            'rate',
            'spread',
            'currency',
        )


class ExchangeRateRetrieveSerializer(ExchangeRateBaseSerializer):
    currency = serializers.CharField(source='currency.code', default=None)

    class Meta(ExchangeRateBaseSerializer.Meta):
        model = ExchangeRate
        fields = ExchangeRateBaseSerializer.Meta.fields


class BillingExchangeRateBaseSerializer(serializers.ModelSerializer):
    rates = ExchangeRateBaseSerializer(many=True)

    class Meta:
        model = BillingExchangeRate
        fields = (
            'id',
            'date',
            'rates',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        company = user.get_company()
        rates = validated_data.pop('rates', [])
        billing_exchange_rate = BillingExchangeRate.objects.filter(
            date=timezone.localtime().date(),
            company=company,
        ).first()
        if billing_exchange_rate:
            billing_exchange_rate.rates.all().delete()
        else:
            validated_data['company'] = company
            billing_exchange_rate = super().create(validated_data)
        rates = [{**item, **{'billing_exchange_rate': billing_exchange_rate}} for item in rates]
        new_rates = [ExchangeRate(**fields) for fields in rates]
        ExchangeRate.objects.bulk_create(new_rates)
        return billing_exchange_rate


class BillingExchangeRateListSerializer(BillingExchangeRateBaseSerializer):
    rates = ExchangeRateRetrieveSerializer(many=True)

    class Meta(BillingExchangeRateBaseSerializer.Meta):
        model = BillingExchangeRate
        fields = BillingExchangeRateBaseSerializer.Meta.fields
