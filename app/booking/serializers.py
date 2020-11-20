from rest_framework import serializers

from django.db.models import Min

from app.booking.models import Surcharge, UsageFee, Charge, AdditionalSurcharge, FreightRate, Rate, CargoGroup, Quote, \
    Booking, Status
from app.booking.utils import rate_surcharges_filter
from app.core.models import Shipper
from app.core.serializers import ShipperSerializer
from app.handling.models import ShippingType, ClientPlatformSetting
from app.handling.serializers import ContainerTypesSerializer, CurrencySerializer, CarrierBaseSerializer, \
    PortSerializer, ShippingModeBaseSerializer, PackagingTypeBaseSerializer, ReleaseTypeSerializer


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


class AdditionalSurchargesSerializer(serializers.ModelSerializer):
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
    additional_surcharge = AdditionalSurchargesSerializer()
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
    freight_rate = serializers.IntegerField(required=False)

    class Meta:
        model = FreightRate
        fields = (
            'carrier',
            'shipping_mode',
            'origin',
            'destination',
            'freight_rate',
        )


class SurchargeEditSerializer(SurchargeCheckDatesSerializer):
    class Meta(SurchargeCheckDatesSerializer.Meta):
        model = Surcharge
        fields = SurchargeCheckDatesSerializer.Meta.fields + (
            'id',
            'start_date',
            'expiration_date',
            'temporary',
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
        company = user.get_company()
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
        company = user.get_company()
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


class FreightRateSearchListSerializer(FreightRateListSerializer):
    carrier = serializers.SerializerMethodField()
    origin = PortSerializer()
    destination = PortSerializer()
    company = serializers.CharField(source='company.name')

    class Meta(FreightRateListSerializer.Meta):
        model = FreightRate
        fields = FreightRateListSerializer.Meta.fields + (
            'transit_time',
            'company',
        )

    def get_carrier(self, obj):
        hide_carrier_name = ClientPlatformSetting.objects.first().hide_carrier_name
        return 'disclosed' if obj.carrier_disclosure or hide_carrier_name else obj.carrier.title


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
            'temporary',
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
        company = user.get_company()
        validated_data['company'] = company
        rates = validated_data.pop('rates', [])
        temporary = validated_data.get('temporary')
        temporary = temporary if temporary else False
        if not temporary:
            errors = {}
            empty_rates = []
            if validated_data['shipping_mode'].has_freight_containers:
                existing_freight_rates = FreightRate.objects.filter(
                    **{key: value for key, value in validated_data.items()
                       if key not in ('transit_time', 'carrier_disclosure')},
                    temporary=False,
                )
                new_not_empty_rates = list(filter(lambda x: x.get('start_date'), rates))
                for existing_freight_rate in existing_freight_rates:
                    for new_rate in new_not_empty_rates:
                        if existing_freight_rate.rates.filter(
                                container_type=new_rate.get('container_type'),
                                start_date__isnull=True
                        ).exists():
                            empty_rates.append(new_rate.get('container_type').id)
            if empty_rates:
                errors['existing_empty_rates'] = list(set(empty_rates))
                raise serializers.ValidationError(errors)
        new_freight_rate = super().create(validated_data)
        rates = [{**item, **{'freight_rate': new_freight_rate, 'updated_by': user}} for item in rates]
        new_rates = [Rate(**fields) for fields in rates]
        for rate in new_rates:
            rate.save()
            if rate.start_date and rate.expiration_date:
                surcharges = rate_surcharges_filter(rate, company, temporary=temporary)
                rate.surcharges.set(surcharges)
        return new_freight_rate


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


class CargoGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoGroup
        fields = (
            'container_type',
            'packaging_type',
            'weight_measurement',
            'length_measurement',
            'volume',
            'height',
            'length',
            'width',
            'weight',
            'total_wm',
            'dangerous',
            'description',
            'frozen',
        )


class CargoGroupRetrieveSerializer(CargoGroupSerializer):
    container_type = ContainerTypesSerializer()
    packaging_type = PackagingTypeBaseSerializer()

    class Meta:
        model = CargoGroup
        fields = CargoGroupSerializer.Meta.fields


class FreightRateSearchSerializer(serializers.Serializer):
    shipping_mode = serializers.IntegerField()
    origin = serializers.IntegerField()
    destination = serializers.IntegerField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    carrier = serializers.IntegerField(required=False)
    cargo_groups = CargoGroupSerializer(many=True)


class WMCalculateSerializer(serializers.Serializer):
    shipping_type = serializers.ChoiceField(choices=ShippingType.objects.values_list('title', flat=True))
    weight_measurement = serializers.ChoiceField(choices=CargoGroup.WEIGHT_MEASUREMENT_CHOICES)
    length_measurement = serializers.ChoiceField(choices=CargoGroup.LENGTH_MEASUREMENT_CHOICES)
    weight = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0)
    height = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0)
    length = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0)
    width = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0)
    volume = serializers.IntegerField(min_value=1)


class QuoteSerializer(serializers.ModelSerializer):
    cargo_groups = CargoGroupSerializer(source='quote_cargo_groups', many=True)

    class Meta:
        model = Quote
        fields = (
            'id',
            'origin',
            'destination',
            'shipping_mode',
            'date_from',
            'date_to',
            'is_active',
            'cargo_groups',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        company = user.get_company()
        validated_data['company'] = company
        cargo_groups = validated_data.pop('quote_cargo_groups', [])
        quote = super().create(validated_data)
        cargo_groups = [{**item, **{'quote': quote}} for item in cargo_groups]
        new_cargo_groups = [CargoGroup(**fields) for fields in cargo_groups]
        CargoGroup.objects.bulk_create(new_cargo_groups)
        return quote


class QuoteListBaseSerializer(QuoteSerializer):
    cargo_groups = CargoGroupRetrieveSerializer(source='quote_cargo_groups', many=True)
    origin = PortSerializer()
    destination = PortSerializer()
    shipping_mode = ShippingModeBaseSerializer()
    shipping_type = serializers.CharField(source='shipping_mode.shipping_type.title')
    week_range = serializers.SerializerMethodField()

    class Meta(QuoteSerializer.Meta):
        model = Quote
        fields = QuoteSerializer.Meta.fields + (
            'shipping_type',
            'week_range',
        )

    def get_week_range(self, obj):
        return {
            'week_from': obj.date_from.isocalendar()[1],
            'week_to': obj.date_to.isocalendar()[1]
        }


class QuoteAgentListSerializer(QuoteListBaseSerializer):
    is_submitted = serializers.SerializerMethodField()

    class Meta(QuoteListBaseSerializer):
        model = Quote
        fields = QuoteListBaseSerializer.Meta.fields + (
            'is_submitted',
        )

    def get_is_submitted(self, obj):
        user = self.context['request'].user
        return True if obj.statuses.filter(freight_rate__company=user.get_company()).exists() else False


class QuoteAgentRetrieveSerializer(QuoteAgentListSerializer):
    status = serializers.SerializerMethodField()

    class Meta(QuoteAgentListSerializer):
        model = Quote
        fields = QuoteAgentListSerializer.Meta.fields + (
            'status',
        )

    def get_status(self, obj):
        company = self.context['request'].user.get_company()
        quote_status = obj.statuses.filter(status=Status.SUBMITTED, freight_rate__company=company).first()
        return QuoteStatusRetrieveSerializer(quote_status).data if quote_status else {}


class QuoteClientListOrRetrieveSerializer(QuoteListBaseSerializer):
    statuses = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    unchecked_offers = serializers.SerializerMethodField()

    class Meta(QuoteListBaseSerializer):
        model = Quote
        fields = QuoteListBaseSerializer.Meta.fields + (
            'statuses',
            'offers',
            'unchecked_offers',
        )

    def get_statuses(self, obj):
        queryset = obj.statuses.filter(status=Status.SUBMITTED)
        return QuoteStatusRetrieveSerializer(queryset, many=True).data if queryset else []

    def get_offers(self, obj):
        return obj.statuses.filter(status=Status.SUBMITTED).count()

    def get_unchecked_offers(self, obj):
        return obj.statuses.filter(status=Status.SUBMITTED, is_viewed=False).count()


class BookingSerializer(serializers.ModelSerializer):
    aceid = serializers.SerializerMethodField()
    shipper = ShipperSerializer()
    cargo_groups = CargoGroupSerializer(many=True)

    class Meta:
        model = Booking
        fields = (
            'id',
            'aceid',
            'date_from',
            'date_to',
            'release_type',
            'number_of_documents',
            'freight_rate',
            'shipper',
            'cargo_groups',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        company = user.get_company()
        validated_data['company'] = company
        shipper = validated_data.pop('shipper')
        shipper['company'] = company
        new_shipper = Shipper.objects.create(**shipper)
        validated_data['shipper'] = new_shipper
        cargo_groups = validated_data.pop('cargo_groups', [])
        booking = super().create(validated_data)
        cargo_groups = [{**item, **{'booking': booking}} for item in cargo_groups]
        new_cargo_groups = [CargoGroup(**fields) for fields in cargo_groups]
        CargoGroup.objects.bulk_create(new_cargo_groups)
        return booking

    def get_aceid(self, obj):
        return f'CO5K5647'


class BookingListBaseSerializer(BookingSerializer):
    week_range = serializers.SerializerMethodField()
    freight_rate = FreightRateRetrieveSerializer()
    shipping_type = serializers.CharField(source='freight_rate.shipping_mode.shipping_type.title')
    client = serializers.CharField(source='company.name')
    status = serializers.SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        model = Booking
        fields = BookingSerializer.Meta.fields + (
            'week_range',
            'freight_rate',
            'shipping_type',
            'client',
            'status',
        )

    def get_week_range(self, obj):
        return {
            'week_from': obj.date_from.isocalendar()[1],
            'week_to': obj.date_to.isocalendar()[1]
        }

    def get_status(self, obj):
        return list(filter(lambda x: x[0] == obj.status, Booking.STATUS_CHOICES))[0][1]


class BookingRetrieveSerializer(BookingListBaseSerializer):
    release_type = ReleaseTypeSerializer()
    shipper = ShipperSerializer()
    cargo_groups = CargoGroupRetrieveSerializer(many=True)

    class Meta(BookingListBaseSerializer.Meta):
        model = Booking
        fields = BookingListBaseSerializer.Meta.fields + (
            'release_type',
            'shipper',
        )


class QuoteStatusBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = (
            'id',
            'quote',
            'freight_rate',
            'company',
            'status',
            'is_viewed',
            'charges',
        )


class QuoteStatusRetrieveSerializer(QuoteStatusBaseSerializer):
    freight_rate = FreightRateRetrieveSerializer()

    class Meta(QuoteStatusBaseSerializer.Meta):
        fields = QuoteStatusBaseSerializer.Meta.fields
        model = Status
