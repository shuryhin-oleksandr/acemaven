from datetime import timedelta

from rest_framework import serializers

from django.db import transaction
from django.db.models import Min
from django.utils import timezone

from app.booking.models import Surcharge, UsageFee, Charge, AdditionalSurcharge, FreightRate, Rate, CargoGroup, Quote, \
    Booking, Status, ShipmentDetails, CancellationReason, Track, TrackStatus
from app.booking.tasks import send_awb_number_to_air_tracking_api
from app.booking.utils import rate_surcharges_filter, calculate_freight_rate_charges, get_fees, generate_aceid
from app.core.models import Shipper
from app.core.serializers import ShipperSerializer, BankAccountBaseSerializer
from app.core.utils import get_average_company_rating
from app.handling.models import ShippingType, ClientPlatformSetting, Currency, GeneralSetting, BillingExchangeRate
from app.handling.serializers import ContainerTypesSerializer, CurrencySerializer, CarrierBaseSerializer, \
    PortSerializer, ShippingModeBaseSerializer, PackagingTypeBaseSerializer, ReleaseTypeSerializer
from app.location.models import Country


main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


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


class GetTrackingInitialMixin:
    """
    Class, that provides initial tracking data.
    """

    def get_tracking_initial(self, obj):
        data = dict()
        data['shipping_type'] = obj.freight_rate.shipping_mode.shipping_type.title
        data['direction'] = 'export' if obj.freight_rate.origin.code.startswith(MAIN_COUNTRY_CODE) else 'import'
        data['origin'] = obj.freight_rate.origin.get_lat_long_coordinates()
        data['destination'] = obj.freight_rate.destination.get_lat_long_coordinates()
        return data


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
        super().update(instance, validated_data)
        surcharges = rate_surcharges_filter(instance, company)
        instance.surcharges.set(surcharges)
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
    company = serializers.SerializerMethodField()

    class Meta(FreightRateListSerializer.Meta):
        model = FreightRate
        fields = FreightRateListSerializer.Meta.fields + (
            'transit_time',
            'company',
        )

    def get_carrier(self, obj):
        hide_carrier_name = ClientPlatformSetting.load().hide_carrier_name
        return 'disclosed' if obj.carrier_disclosure or hide_carrier_name else obj.carrier.title

    def get_company(self, obj):
        company_data = dict()
        general_settings = GeneralSetting.load()
        show_freight_forwarder_name = general_settings.show_freight_forwarder_name
        name = obj.company.name if show_freight_forwarder_name == GeneralSetting.ALL else '*Agent company name'
        company_data['name'] = name
        company_data['id'] = obj.company.id
        company_data['rating'] = get_average_company_rating(obj.company)
        return company_data


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
                    is_archived=False,
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
            'id',
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
            'booking',
        )


class CargoGroupWithIdSerializer(CargoGroupSerializer):
    id = serializers.IntegerField(required=False)

    class Meta(CargoGroupSerializer.Meta):
        model = CargoGroup
        fields = CargoGroupSerializer.Meta.fields


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


class OperationRecalculateSerializer(serializers.Serializer):
    number_of_documents = serializers.IntegerField(min_value=1, required=False)
    cargo_groups = CargoGroupWithIdSerializer(many=True)


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


class CancellationReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancellationReason
        fields = (
            'id',
            'reason',
            'comment',
            'agent_contact_person',
        )


class BookingSerializer(serializers.ModelSerializer):
    shipper = ShipperSerializer(required=False)
    cargo_groups = CargoGroupSerializer(many=True)
    existing_shipper = serializers.PrimaryKeyRelatedField(
        queryset=Shipper.objects.all(),
        write_only=True,
        required=False
    )

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
            'existing_shipper',
            'cargo_groups',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        company = user.get_company()
        validated_data['client_contact_person'] = user

        existing_shipper = validated_data.pop('existing_shipper', None)
        if not existing_shipper:
            shipper = validated_data.pop('shipper', {})
            shipper['company'] = company
            shipper['is_partner'] = False if validated_data['freight_rate'].origin.code.startswith(MAIN_COUNTRY_CODE) \
                else True
            existing_shipper = Shipper.objects.create(**shipper)

        validated_data['shipper'] = existing_shipper
        cargo_groups = validated_data.pop('cargo_groups', [])

        changed_cargo_groups = CargoGroupSerializer(cargo_groups, many=True).data
        main_currency_code = Currency.objects.filter(is_main=True).first().code
        container_type_ids_list = [
            group.get('container_type') for group in changed_cargo_groups if 'container_type' in group
        ]
        freight_rate = validated_data.get('freight_rate')
        booking_fee, service_fee = get_fees(company, freight_rate.shipping_mode)
        number_of_documents = validated_data.get('number_of_documents')
        calculate_fees = ClientPlatformSetting.load().enable_booking_fee_payment
        try:
            with transaction.atomic():
                result = calculate_freight_rate_charges(freight_rate,
                                                        {},
                                                        changed_cargo_groups,
                                                        freight_rate.shipping_mode,
                                                        main_currency_code,
                                                        validated_data.get('date_from'),
                                                        validated_data.get('date_to'),
                                                        container_type_ids_list,
                                                        number_of_documents=number_of_documents,
                                                        booking_fee=booking_fee,
                                                        service_fee=service_fee,
                                                        calculate_fees=calculate_fees,)
                if result.get('pay_to_book', {}).get('pay_to_book', 0) == 0:
                    validated_data['is_paid'] = True
                    validated_data['status'] = Booking.REQUEST_RECEIVED
                    result.pop('pay_to_book', None)
                validated_data['charges'] = result
                validated_data['aceid'] = generate_aceid(freight_rate, company)
                booking = super().create(validated_data)

                cargo_groups = [{**item, **{'booking': booking}} for item in cargo_groups]
                new_cargo_groups = [CargoGroup(**fields) for fields in cargo_groups]
                CargoGroup.objects.bulk_create(new_cargo_groups)
        except Exception as error:
            raise serializers.ValidationError({'error': error})
        return booking


class BookingListBaseSerializer(BookingSerializer):
    week_range = serializers.SerializerMethodField()
    freight_rate = FreightRateRetrieveSerializer()
    cargo_groups = CargoGroupRetrieveSerializer(many=True)
    shipping_type = serializers.CharField(source='freight_rate.shipping_mode.shipping_type.title')
    client = serializers.CharField(source='client_contact_person.get_company.name')
    status = serializers.SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        model = Booking
        fields = BookingSerializer.Meta.fields + (
            'week_range',
            'freight_rate',
            'shipping_type',
            'client',
            'status',
            'aceid',
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
    client_contact_person = serializers.CharField(source='client_contact_person.get_full_name')
    agent_contact_person = serializers.CharField(source='agent_contact_person.get_full_name', default=None)

    class Meta(BookingListBaseSerializer.Meta):
        model = Booking
        fields = BookingListBaseSerializer.Meta.fields + (
            'release_type',
            'shipper',
            'client_contact_person',
            'agent_contact_person',
            'is_assigned',
            'is_paid',
            'charges',
        )


class ShipmentDetailsBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentDetails
        fields = (
            'id',
            'booking_number',
            'booking_number_with_carrier',
            'flight_number',
            'vessel',
            'voyage',
            'container_number',
            'mawb',
            'date_of_departure',
            'date_of_arrival',
            'actual_date_of_departure',
            'actual_date_of_arrival',
            'document_cut_off_date',
            'cargo_cut_off_date',
            'cargo_pick_up_location',
            'cargo_pick_up_location_address',
            'cargo_drop_off_location',
            'cargo_drop_off_location_address',
            'empty_pick_up_location',
            'empty_pick_up_location_address',
            'container_free_time',
            'booking_notes',
            'booking',
        )

    def create(self, validated_data):
        shipment_detail = super().create(validated_data)
        booking = validated_data['booking']
        booking.status = Booking.CONFIRMED
        carrier = booking.freight_rate.carrier
        if carrier.scac or carrier.code:
            booking.automatic_tracking = True
        booking.save()
        if booking.shipping_type == 'air' and booking.automatic_tracking:
            send_awb_number_to_air_tracking_api.delay(shipment_detail.booking_number)
        return shipment_detail

    def update(self, instance, validated_data):
        user = self.context['request'].user
        departure_track_exists = Track.objects.filter(
            manual=True,
            booking=instance.booking,
            status=TrackStatus.objects.filter(
                shipping_mode=instance.booking.freight_rate.shipping_mode,
                auto_add_on_actual_date_of_departure=True,
            ).first(),
        ).exists()
        arrival_track_exists = Track.objects.filter(
            manual=True,
            booking=instance.booking,
            status=TrackStatus.objects.filter(
                shipping_mode=instance.booking.freight_rate.shipping_mode,
                auto_add_on_actual_date_of_arrival=True,
            ).first(),
        ).exists()
        create_track = False
        if validated_data.get('actual_date_of_departure') and not departure_track_exists:
            track_status = TrackStatus.objects.filter(
                shipping_mode=instance.booking.freight_rate.shipping_mode,
                auto_add_on_actual_date_of_departure=True,
            ).first()
            create_track = True
        elif validated_data.get('actual_date_of_arrival') and not arrival_track_exists:
            track_status = TrackStatus.objects.filter(
                shipping_mode=instance.booking.freight_rate.shipping_mode,
                auto_add_on_actual_date_of_arrival=True,
            ).first()
            create_track = True
        if create_track:
            Track.objects.create(
                manual=True,
                created_by=user,
                status=track_status,
                booking=instance.booking,
            )
        super().update(instance, validated_data)
        return instance


class TrackSerializer(serializers.ModelSerializer):
    actual_date_of_departure = serializers.DateTimeField(write_only=True, required=False)
    actual_date_of_arrival = serializers.DateTimeField(write_only=True, required=False)

    class Meta:
        model = Track
        fields = (
            'id',
            'date_created',
            'data',
            'route',
            'comment',
            'status',
            'booking',
            'actual_date_of_departure',
            'actual_date_of_arrival',
        )

    def create(self, validated_data):
        validated_data['manual'] = True
        validated_data['created_by'] = self.context['request'].user
        actual_date_of_departure = validated_data.pop('actual_date_of_departure', None)
        actual_date_of_arrival = validated_data.pop('actual_date_of_arrival', None)

        status = validated_data['status']
        shipment_details = validated_data['booking'].shipment_details.first()

        if status.must_update_actual_date_of_departure:
            shipment_details.actual_date_of_departure = timezone.localtime()

        elif status.auto_add_on_actual_date_of_departure and actual_date_of_departure:
            shipment_details.actual_date_of_departure = actual_date_of_departure

        elif status.auto_add_on_actual_date_of_arrival and actual_date_of_arrival:
            shipment_details.actual_date_of_arrival = actual_date_of_arrival

        shipment_details.save()

        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        validated_data['manual'] = True
        instance = super().update(instance, validated_data)
        return instance


class TrackRetrieveSerializer(TrackSerializer):
    status = serializers.CharField(source='status.title', default=None)
    created_by = serializers.CharField(source='created_by.get_full_name', default=None)

    class Meta(TrackSerializer.Meta):
        model = Track
        fields = TrackSerializer.Meta.fields + (
            'created_by',
        )


class TrackWidgetListSerializer(serializers.ModelSerializer):
    shipping_type = serializers.CharField(source='booking.freight_rate.shipping_mode.shipping_type', default=None)
    booking_number = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()
    status = serializers.CharField(source='status.title', default=None)

    class Meta:
        model = Track
        fields = (
            'shipping_type',
            'booking_number',
            'route',
            'date_created',
            'status',
        )

    def get_booking_number(self, obj):
        return obj.booking.shipment_details.first().booking_number if obj.booking else None

    def get_route(self, obj):
        return f'{booking.freight_rate.origin.code}-' \
               f'{booking.freight_rate.destination.code}' if (booking := obj.booking) else None


class TrackStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackStatus
        fields = (
            'id',
            'title',
        )


class OperationSerializer(serializers.ModelSerializer):
    cargo_groups = CargoGroupSerializer(many=True)

    class Meta:
        model = Booking
        fields = (
            'id',
            'aceid',
            'cargo_groups',
            'date_from',
            'date_to',
            'payment_due_by',
            'is_assigned',
            'release_type',
            'number_of_documents',
            'freight_rate',
            'shipper',
            'original_booking',
        )

    def create(self, validated_data):
        cargo_groups = validated_data.pop('cargo_groups', [])
        changed_cargo_groups = CargoGroupSerializer(cargo_groups, many=True).data
        number_of_documents = validated_data.get('number_of_documents')
        main_currency_code = Currency.objects.filter(is_main=True).first().code
        container_type_ids_list = [
            group.get('container_type') for group in changed_cargo_groups if 'container_type' in group
        ]
        freight_rate = validated_data.get('freight_rate')
        original_booking = validated_data.get('original_booking')
        validated_data['status'] = original_booking.status
        validated_data['agent_contact_person'] = original_booking.agent_contact_person
        validated_data['client_contact_person'] = original_booking.client_contact_person
        try:
            with transaction.atomic():
                result = calculate_freight_rate_charges(freight_rate,
                                                        {},
                                                        changed_cargo_groups,
                                                        freight_rate.shipping_mode,
                                                        main_currency_code,
                                                        original_booking.date_from,
                                                        original_booking.date_to,
                                                        container_type_ids_list,
                                                        number_of_documents=number_of_documents,)
                validated_data['charges'] = result
                validated_data['is_paid'] = True
                validated_data['is_assigned'] = True
                operation = super().create(validated_data)

                cargo_groups = [{**item, **{'booking': operation}} for item in cargo_groups]
                new_cargo_groups = [CargoGroup(**fields) for fields in cargo_groups]
                CargoGroup.objects.bulk_create(new_cargo_groups)
        except Exception as error:
            raise serializers.ValidationError({'error': error})
        original_booking.change_request_status = Booking.CHANGE_REQUESTED
        original_booking.save()
        return operation


class OperationListBaseSerializer(GetTrackingInitialMixin, OperationSerializer):
    freight_rate = FreightRateRetrieveSerializer()
    shipping_type = serializers.CharField(source='freight_rate.shipping_mode.shipping_type.title')
    status = serializers.SerializerMethodField()
    agent_contact_person = serializers.CharField(source='agent_contact_person.get_full_name', default=None)
    cargo_groups = CargoGroupRetrieveSerializer(many=True)
    shipment_details = ShipmentDetailsBaseSerializer(many=True)
    has_change_request = serializers.SerializerMethodField()
    can_be_patched = serializers.SerializerMethodField()
    tracking_initial = serializers.SerializerMethodField()
    tracking = TrackRetrieveSerializer(many=True)

    class Meta(OperationSerializer.Meta):
        model = Booking
        fields = OperationSerializer.Meta.fields + (
            'shipping_type',
            'status',
            'agent_contact_person',
            'shipment_details',
            'has_change_request',
            'can_be_patched',
            'tracking_initial',
            'tracking',
            'automatic_tracking',
        )

    def get_status(self, obj):
        if change_request_status := obj.change_request_status:
            return list(filter(lambda x: x[0] == change_request_status, Booking.CHANGE_REQUESTED_CHOICES))[0][1]
        return list(filter(lambda x: x[0] == obj.status, Booking.STATUS_CHOICES))[0][1]

    def get_has_change_request(self, obj):
        return True if obj.change_requests.exists() else False

    def get_can_be_patched(self, obj):
        return True if obj.status in (Booking.PENDING, Booking.REQUEST_RECEIVED) else False


class OperationRetrieveSerializer(OperationListBaseSerializer):
    release_type = ReleaseTypeSerializer()
    week_range = serializers.SerializerMethodField()
    client_contact_person = serializers.CharField(source='client_contact_person.get_full_name')
    client = serializers.CharField(source='client_contact_person.get_company.name')
    charges_today = serializers.SerializerMethodField()
    shipper = ShipperSerializer()
    change_requests = serializers.SerializerMethodField()
    chat = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta(OperationListBaseSerializer.Meta):
        model = Booking
        fields = OperationListBaseSerializer.Meta.fields + (
            'week_range',
            'client_contact_person',
            'client',
            'charges_today',
            'charges',
            'change_requests',
            'chat',
        )

    def get_change_requests(self, obj):
        serializer = OperationRetrieveSerializer(obj.change_requests.all(), many=True)
        return serializer.data

    def get_week_range(self, obj):
        return {
            'week_from': obj.date_from.isocalendar()[1],
            'week_to': obj.date_to.isocalendar()[1]
        }

    def get_charges_today(self, obj):
        result = dict()
        if obj.agent_contact_person:
            company = obj.agent_contact_person.get_company()
            totals = obj.charges.get('totals')
            billing_exchange_rate = BillingExchangeRate.objects.filter(company=company).first()
            if billing_exchange_rate:
                main_currency_code = Currency.objects.filter(is_main=True).first().code
                total_today = 0
                for key, value in totals.items():
                    rate_today = 1
                    if key != main_currency_code:
                        rate = billing_exchange_rate.rates.filter(currency__code=key).first()
                        rate_today = round(float(rate.rate) * (1 + float(rate.spread) / 100), 2)
                        result[f'{key} exchange rate'] = rate_today
                    total_today += value * rate_today
                result['total_today'] = total_today
        return result


class OperationRetrieveClientSerializer(OperationRetrieveSerializer):
    agent_bank_account = serializers.SerializerMethodField()
    tracking = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()

    class Meta(OperationRetrieveSerializer.Meta):
        model = Booking
        fields = OperationRetrieveSerializer.Meta.fields + (
            'agent_bank_account',
            'has_review',
        )

    def get_agent_bank_account(self, obj):
        if obj.agent_contact_person:
            bank_account = obj.agent_contact_person.get_company().bank_accounts.filter(is_default=True).first()
            if bank_account:
                return BankAccountBaseSerializer(bank_account).data
        return {}

    def get_tracking(self, obj):
        serializer = TrackRetrieveSerializer(
            obj.tracking.filter(date_created__lt=timezone.localtime()-timedelta(minutes=5)),
            many=True
        )
        return serializer.data

    def get_has_review(self,  obj):
        return True if hasattr(obj, 'review') else False


class OperationBillingBaseSerializer(serializers.ModelSerializer):
    origin = PortSerializer(source='freight_rate.origin')
    destination = PortSerializer(source='freight_rate.destination')
    shipping_type = serializers.CharField(source='freight_rate.shipping_mode.shipping_type.title')
    shipping_mode = serializers.CharField(source='freight_rate.shipping_mode.title')
    status = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id',
            'aceid',
            'origin',
            'destination',
            'shipping_type',
            'shipping_mode',
            'charges',
            'status',
            'payment_due_by',
        )

    def get_status(self, obj):
        if change_request_status := obj.change_request_status:
            return list(filter(lambda x: x[0] == change_request_status, Booking.CHANGE_REQUESTED_CHOICES))[0][1]
        return list(filter(lambda x: x[0] == obj.status, Booking.STATUS_CHOICES))[0][1]


class OperationBillingAgentListSerializer(OperationBillingBaseSerializer):
    carrier = serializers.CharField(source='freight_rate.carrier.title')
    client = serializers.CharField(source='client_contact_person.get_company.name')
    booking_number = serializers.SerializerMethodField()
    vessel = serializers.SerializerMethodField()

    class Meta(OperationBillingBaseSerializer.Meta):
        model = Booking
        fields = OperationBillingBaseSerializer.Meta.fields + (
            'carrier',
            'client',
            'booking_number',
            'vessel',
        )

    def get_booking_number(self, obj):
        shipment_detail = obj.shipment_details.first()
        return shipment_detail.booking_number if shipment_detail else None

    def get_vessel(self, obj):
        shipment_detail = obj.shipment_details.first()
        return shipment_detail.vessel if shipment_detail else None


class OperationBillingClientListSerializer(GetTrackingInitialMixin, OperationBillingBaseSerializer):
    tracking_initial = serializers.SerializerMethodField()
    tracking = TrackRetrieveSerializer(many=True)
    dates = serializers.SerializerMethodField()

    class Meta(OperationBillingBaseSerializer.Meta):
        model = Booking
        fields = OperationBillingBaseSerializer.Meta.fields + (
            'tracking_initial',
            'tracking',
            'dates',
            'date_created',
        )

    def get_dates(self, obj):
        shipment_details = obj.shipment_details.first()
        return f'ETD: {shipment_details.date_of_departure.strftime("%d/%m")}, ' \
               f'ETA: {shipment_details.date_of_arrival.strftime("%d/%m")}' if shipment_details else None


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
