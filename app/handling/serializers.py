from rest_framework import serializers

from app.handling.models import Carrier, Port


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
