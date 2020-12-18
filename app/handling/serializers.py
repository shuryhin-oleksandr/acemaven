from rest_framework import serializers

from app.handling.models import Carrier, Port, ShippingMode, ShippingType, ContainerType, Currency, PackagingType, \
    ReleaseType
from app.booking.models import AdditionalSurcharge
from app.location.models import Country


main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


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
    coordinates = serializers.ListField(source='coordinates.coords', default=[])

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
