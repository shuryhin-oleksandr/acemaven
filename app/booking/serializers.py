from rest_framework import serializers

from django.db.models import Min
from django.conf import settings

from app.booking.models import Surcharge, UsageFee, Charge, AdditionalSurcharge, FreightRate, Rate
from app.booking.utils import rate_surcharges_filter
from app.handling.serializers import ContainerTypesSerializer, CurrencySerializer, CarrierBaseSerializer, \
    PortSerializer, ShippingModeBaseSerializer


COUNTRY_CODE = settings.COUNTRY_OF_ORIGIN_CODE


class UserUpdateMixin:
    """
    Class, that provides custom update() method with user saving from request.
    """

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        super().update(instance, validated_data)
        return instance


class UserFullNameGetMixin:
    """
    Class, that provides custom serializer method with user full name.
    """

    def get_updated_by(self, obj):
        if user := obj.updated_by:
            return user.get_full_name()


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


class UsageFeeEditSerializer(UserFullNameGetMixin, UsageFeeSerializer):
    container_type = ContainerTypesSerializer()
    currency = CurrencySerializer()
    updated_by = serializers.SerializerMethodField()

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


class ChargeEditSerializer(UserFullNameGetMixin, ChargeSerializer):
    additional_surcharge = AdditionalSurchargeSerializer()
    currency = CurrencySerializer()
    updated_by = serializers.SerializerMethodField()

    class Meta(ChargeSerializer.Meta):
        model = Charge
        fields = ChargeSerializer.Meta.fields + (
            'updated_by',
            'date_updated',
        )


class SurchargeListSerializer(serializers.ModelSerializer):
    carrier = serializers.CharField(source='carrier.title')
    location = serializers.CharField(source='location.display_name')
    shipping_mode = serializers.CharField(source='shipping_mode.title')
    shipping_type = serializers.CharField(source='shipping_mode.shipping_type.title', initial='')

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


class FreightRateCheckDatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreightRate
        fields = (
            'carrier',
            'shipping_mode',
            'origin',
            'destination',
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


class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = (
            'id',
            'container_type',
            'currency',
            'rate',
            'start_date',
            'expiration_date',
        )

    def update(self, instance, validated_data):
        user = self.context['request'].user
        company = user.companies.first()
        validated_data['updated_by'] = user
        rate = super().update(instance, validated_data)
        surcharges = rate_surcharges_filter(rate, company)
        rate.surcharges.set(surcharges)
        return instance


class RateEditSerializer(UserFullNameGetMixin, RateSerializer):
    container_type = ContainerTypesSerializer()
    currency = CurrencySerializer()
    updated_by = serializers.SerializerMethodField()
    surcharges = SurchargeRetrieveSerializer(many=True)

    class Meta(RateSerializer.Meta):
        model = Rate
        fields = RateSerializer.Meta.fields + (
            'updated_by',
            'date_updated',
            'surcharges',
        )


class FreightRateListSerializer(serializers.ModelSerializer):
    carrier = serializers.CharField(source='carrier.title')
    origin = serializers.CharField(source='origin.display_name')
    destination = serializers.CharField(source='destination.display_name')
    shipping_mode = serializers.CharField(source='shipping_mode.title')
    shipping_type = serializers.CharField(source='shipping_mode.shipping_type.title')
    expiration_date = serializers.SerializerMethodField()

    class Meta:
        model = FreightRate
        fields = (
            'id',
            'carrier',
            'origin',
            'destination',
            'shipping_mode',
            'shipping_type',
            'expiration_date',
            'is_active',
        )

    def get_expiration_date(self, obj):
        date = obj.rates.aggregate(date=Min('expiration_date')).get('date')
        return date.strftime('%d/%m/%Y') if date else None


class FreightRateEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreightRate
        fields = (
            'id',
            'carrier',
            'carrier_disclosure',
            'origin',
            'destination',
            'transit_time',
            'is_active',
            'shipping_mode',
        )


class FreightRateSerializer(FreightRateEditSerializer):
    rates = RateSerializer(many=True)

    class Meta(FreightRateEditSerializer.Meta):
        model = FreightRate
        fields = FreightRateEditSerializer.Meta.fields + (
            'rates',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        company = user.companies.first()
        validated_data['company'] = company
        rates = validated_data.pop('rates', [])
        freight_rate = super().create(validated_data)
        rates = [{**item, **{'freight_rate': freight_rate, 'updated_by': user}} for item in rates]
        new_rates = [Rate(**fields) for fields in rates]
        for rate in new_rates:
            surcharges = rate_surcharges_filter(rate, company)
            rate.save()
            rate.surcharges.set(surcharges)
        return freight_rate


class FreightRateRetrieveSerializer(FreightRateSerializer):
    carrier = CarrierBaseSerializer()
    origin = PortSerializer()
    destination = PortSerializer()
    shipping_mode = ShippingModeBaseSerializer()
    shipping_type = serializers.CharField(source='shipping_mode.shipping_type.title')
    rates = RateEditSerializer(many=True)

    class Meta(FreightRateSerializer.Meta):
        model = FreightRate
        fields = FreightRateSerializer.Meta.fields + (
            'shipping_type',
        )


class CheckRateDateSerializer(serializers.Serializer):
    carrier = serializers.IntegerField()
    origin = serializers.IntegerField()
    destination = serializers.IntegerField()
    shipping_mode = serializers.IntegerField()
    start_date = serializers.DateField()
    expiration_date = serializers.DateField()
