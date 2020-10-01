from rest_framework import serializers

from app.handling.models import Carrier, Port, ShippingMode, ShippingType


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
    class Meta:
        model = ShippingMode
        fields = (
            'id',
            'title',
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
