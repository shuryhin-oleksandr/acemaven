from rest_framework import serializers

from django.db.models import Min

from app.booking.models import Surcharge, UsageFee, Charge, AdditionalSurcharge, FreightRate, Rate
from app.handling.serializers import ContainerTypesSerializer, CurrencySerializer, CarrierBaseSerializer, \
    PortSerializer, ShippingModeBaseSerializer


class UserUpdateMixin:
    """
    Class, that provides custom update() method with user saving from request.
    """

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        super().update(instance, validated_data)
        return instance


class AdditionalSurchargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalSurcharge
        fields = (
            'id',
            'title',
        )


class UsageFeeSerializer(UserUpdateMixin, serializers.ModelSerializer):
    class Meta:
        model = UsageFee
        fields = (
            'id',
            'container_type',
            'currency',
            'charge',
        )


class UsageFeeEditSerializer(UsageFeeSerializer):
    container_type = ContainerTypesSerializer()
    currency = CurrencySerializer()

    class Meta(UsageFeeSerializer.Meta):
        model = UsageFee
        fields = UsageFeeSerializer.Meta.fields + (
            'updated_by',
            'date_updated',
        )


class ChargeSerializer(UserUpdateMixin, serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = (
            'id',
            'additional_surcharge',
            'currency',
            'charge',
            'conditions',
        )


class ChargeEditSerializer(ChargeSerializer):
    additional_surcharge = AdditionalSurchargeSerializer()
    currency = CurrencySerializer()

    class Meta(ChargeSerializer.Meta):
        model = Charge
        fields = ChargeSerializer.Meta.fields + (
            'updated_by',
            'date_updated',
        )


class SurchargeListSerializer(serializers.ModelSerializer):
    carrier = serializers.CharField(source='carrier.title')
    location = serializers.CharField(source='location.code')
    shipping_mode = serializers.CharField(source='shipping_mode.title')
    shipping_type = serializers.CharField(source='shipping_mode.shipping_type.title')

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
            'shipping_type',
        )


class SurchargeCheckDatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Surcharge
        fields = (
            'carrier',
            'direction',
            'shipping_mode',
            'location',
        )


class SurchargeEditSerializer(SurchargeCheckDatesSerializer):
    class Meta(SurchargeCheckDatesSerializer.Meta):
        model = Surcharge
        fields = SurchargeCheckDatesSerializer.Meta.fields + (
            'id',
            'start_date',
            'expiration_date',
        )


class SurchargeSerializer(SurchargeEditSerializer):
    usage_fees = UsageFeeSerializer(many=True, required=False)
    charges = ChargeSerializer(many=True)

    class Meta(SurchargeEditSerializer.Meta):
        model = Surcharge
        fields = SurchargeEditSerializer.Meta.fields + (
            'usage_fees',
            'charges',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        company = user.companies.first()
        validated_data['company'] = company
        usage_fees = validated_data.pop('usage_fees', [])
        charges = validated_data.pop('charges', [])
        surcharge = super().create(validated_data)
        usage_fees = [{**item, **{'surcharge': surcharge, 'updated_by': user}} for item in usage_fees]
        new_usage_fees = [UsageFee(**fields) for fields in usage_fees]
        UsageFee.objects.bulk_create(new_usage_fees)
        charges = [{**item, **{'surcharge': surcharge, 'updated_by': user}} for item in charges]
        new_charges = [Charge(**fields) for fields in charges]
        Charge.objects.bulk_create(new_charges)
        return surcharge


class SurchargeRetrieveSerializer(SurchargeSerializer):
    carrier = CarrierBaseSerializer()
    location = PortSerializer()
    shipping_mode = ShippingModeBaseSerializer()
    shipping_type = serializers.CharField(source='shipping_mode.shipping_type.title')
    usage_fees = UsageFeeEditSerializer(many=True)
    charges = ChargeEditSerializer(many=True)

    class Meta(SurchargeSerializer.Meta):
        model = Surcharge
        fields = SurchargeSerializer.Meta.fields + (
            'shipping_type',
        )


class FreightRateListSerializer(serializers.ModelSerializer):
    carrier = serializers.CharField(source='carrier.title')
    origin = serializers.CharField(source='origin.code')
    destination = serializers.CharField(source='destination.code')
    shipping_mode = serializers.CharField(source='shipping_mode.title')
    expiration_date = serializers.SerializerMethodField()

    class Meta:
        model = FreightRate
        fields = (
            'id',
            'carrier',
            'origin',
            'destination',
            'shipping_mode',
            'expiration_date',
            'is_active',
        )

    def get_expiration_date(self, obj):
        date = obj.rates.aggregate(date=Min('expiration_date')).get('date')
        return date.strftime('%m/%d/%Y') if date else None
