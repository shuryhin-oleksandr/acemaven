from rest_framework import serializers

from app.booking.models import Surcharge, UsageFee, Charge, AdditionalSurcharge
from app.handling.serializers import ContainerTypesSerializer, CurrencySerializer, CarrierBaseSerializer, \
    PortSerializer, ShippingModeBaseSerializer


class AdditionalSurchargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalSurcharge
        fields = (
            'id',
            'title',
        )


class UsageFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageFee
        fields = (
            'id',
            'container_type',
            'surcharge',
            'currency',
            'charge',
        )


class UsageFeeEditSerializer(UsageFeeSerializer):
    container_type = ContainerTypesSerializer()
    currency = CurrencySerializer()

    class Meta(UsageFeeSerializer.Meta):
        model = UsageFee
        fields = UsageFeeSerializer.Meta.fields


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = (
            'id',
            'additional_surcharge',
            'surcharge',
            'currency',
            'charge',
            'conditions',
        )


class ChargeEditSerializer(ChargeSerializer):
    additional_surcharge = AdditionalSurchargeSerializer()
    currency = CurrencySerializer()

    class Meta(ChargeSerializer.Meta):
        model = Charge
        fields = ChargeSerializer.Meta.fields


class SurchargeListSerializer(serializers.ModelSerializer):
    carrier = serializers.CharField(source='carrier.title')
    location = serializers.CharField(source='location.code')
    shipping_mode = serializers.CharField(source='shipping_mode.title')

    class Meta:
        model = Surcharge
        fields = (
            'id',
            'carrier',
            'direction',
            'location',
            'start_date',
            'expiration_date',
            'shipping_mode',
        )


class SurchargeEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Surcharge
        fields = (
            'id',
            'carrier',
            'direction',
            'location',
            'start_date',
            'expiration_date',
            'shipping_mode',
            'carrier_disclosure',
        )


class SurchargeSerializer(SurchargeEditSerializer):
    usage_fees = UsageFeeSerializer(many=True)
    charges = ChargeSerializer(many=True)

    class Meta(SurchargeEditSerializer):
        model = Surcharge
        fields = SurchargeEditSerializer.Meta.fields + (
            'usage_fees',
            'charges',
        )

    def create(self, validated_data):
        company = self.context['request'].user.companies.first()
        validated_data['company'] = company
        usage_fees = validated_data.pop('usage_fees', [])
        charges = validated_data.pop('charges', [])
        surcharge = super().create(validated_data)
        usage_fees = [{**item, **{'surcharge': surcharge}} for item in usage_fees]
        new_usage_fees = [UsageFee(**fields) for fields in usage_fees]
        UsageFee.objects.bulk_create(new_usage_fees)
        charges = [{**item, **{'surcharge': surcharge}} for item in charges]
        new_charges = [Charge(**fields) for fields in charges]
        Charge.objects.bulk_create(new_charges)
        return surcharge


class SurchargeRetrieveSerializer(SurchargeSerializer):
    carrier = CarrierBaseSerializer()
    location = PortSerializer()
    shipping_mode = ShippingModeBaseSerializer()
    usage_fees = UsageFeeEditSerializer(many=True)
    charges = ChargeEditSerializer(many=True)

    class Meta(SurchargeSerializer.Meta):
        model = Surcharge
        fields = SurchargeSerializer.Meta.fields
