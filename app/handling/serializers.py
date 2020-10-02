from rest_framework import serializers

from app.handling.models import Carrier, Port, ShippingMode, ShippingType, ContainerType
from app.booking.serializers import AdditionalSurchargeSerializer


class ContainerTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerType
        fields = (
            'id',
            'code',
        )


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = (
            'id',
            'title',
            'shipping_type',
        )


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = (
            'id',
            'code',
            'name',
        )


class ShippingModeSerializer(serializers.ModelSerializer):
    additional_surcharges = AdditionalSurchargeSerializer(many=True)
    container_types = ContainerTypesSerializer(many=True)

    class Meta:
        model = ShippingMode
        fields = (
            'id',
            'title',
            'additional_surcharges',
            'container_types',
        )


class ShippingTypeSerializer(serializers.ModelSerializer):
    shipping_modes = ShippingModeSerializer(many=True)

    class Meta:
        model = ShippingType
        fields = (
            'id',
            'title',
            'shipping_modes',
        )
