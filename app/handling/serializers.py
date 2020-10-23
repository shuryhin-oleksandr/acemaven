from rest_framework import serializers

from app.handling.models import Carrier, Port, ShippingMode, ShippingType, ContainerType, Currency, PackagingType
from app.booking.models import AdditionalSurcharge


class AdditionalSurchargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalSurcharge
        fields = (
            'id',
            'title',
        )


class ContainerTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerType
        fields = (
            'id',
            'code',
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
    is_local = serializers.BooleanField(read_only=True)

    class Meta:
        model = Port
        fields = (
            'id',
            'code',
            'name',
            'display_name',
            'is_local',
        )


class ShippingModeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMode
        fields = (
            'id',
            'title',
        )


class ShippingModeSerializer(ShippingModeBaseSerializer):
    container_types = serializers.SerializerMethodField()
    additional_surcharges = AdditionalSurchargeSerializer(many=True)

    class Meta(ShippingModeBaseSerializer.Meta):
        fields = ShippingModeBaseSerializer.Meta.fields + (
            'container_types',
            'additional_surcharges',
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


class PackagingTypeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = (
            'id',
            'code',
        )
