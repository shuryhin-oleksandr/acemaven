from datetime import datetime

from django_filters import rest_framework
from rest_framework import mixins, viewsets, filters, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import CharField, Case, When, Value, Q, Count

from app.booking.filters import SurchargeFilterSet, FreightRateFilterSet, QuoteFilterSet, QuoteOrderingFilterBackend
from app.booking.mixins import FeeGetQuerysetMixin
from app.booking.models import Surcharge, UsageFee, Charge, FreightRate, Rate, Quote, Booking, Status
from app.booking.serializers import SurchargeSerializer, SurchargeEditSerializer, SurchargeListSerializer, \
    SurchargeRetrieveSerializer, UsageFeeSerializer, ChargeSerializer, FreightRateListSerializer, \
    SurchargeCheckDatesSerializer, FreightRateEditSerializer, FreightRateSerializer, FreightRateRetrieveSerializer, \
    RateSerializer, CheckRateDateSerializer, FreightRateCheckDatesSerializer, WMCalculateSerializer, \
    FreightRateSearchSerializer, FreightRateSearchListSerializer, QuoteSerializer, BookingSerializer, \
    QuoteListSerializer, QuoteAgentListOrRetrieveSerializer
from app.booking.utils import date_format, wm_calculate, calculate_additional_surcharges, calculate_freight_rate, \
    add_currency_value, freight_rate_search
from app.core.mixins import PermissionClassByActionMixin
from app.core.models import Company
from app.core.permissions import IsMasterOrAgent, IsClientCompany, IsAgentCompany
from app.handling.models import Port, GlobalFee, ExchangeRate, Currency, ContainerType, PackagingType, \
    ClientPlatformSetting
from app.location.models import Country


main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


class SurchargeViesSet(viewsets.ModelViewSet):
    queryset = Surcharge.objects.all()
    serializer_class = SurchargeSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )
    filter_class = SurchargeFilterSet
    filter_backends = (filters.OrderingFilter, rest_framework.DjangoFilterBackend,)
    ordering_fields = ('shipping_mode', 'carrier', 'location', 'start_date', 'expiration_date', )

    def get_serializer_class(self):
        if self.action == 'list':
            return SurchargeListSerializer
        if self.action == 'retrieve':
            return SurchargeRetrieveSerializer
        if self.action in ('update', 'partial_update'):
            return SurchargeEditSerializer
        return self.serializer_class

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(company=user.companies.first())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        new_surcharge_id = serializer.data.get('id')
        surcharge = Surcharge.objects.get(id=new_surcharge_id)
        data = SurchargeRetrieveSerializer(surcharge).data
        return Response(data=data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['post'], detail=False, url_path='check-date')
    def check_date(self, request, *args, **kwargs):
        serializer = SurchargeCheckDatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        dates = self.get_queryset().filter(**data).order_by('start_date').values('start_date', 'expiration_date')
        results = [{key: value.strftime('%m/%d/%Y') for key, value in item.items()} for item in dates]
        return Response(data=results, status=status.HTTP_201_CREATED)


class UsageFeeViesSet(FeeGetQuerysetMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    queryset = UsageFee.objects.all()
    serializer_class = UsageFeeSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )


class ChargeViesSet(FeeGetQuerysetMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = Charge.objects.all()
    serializer_class = ChargeSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )


class FreightRateViesSet(PermissionClassByActionMixin,
                         viewsets.ModelViewSet):
    queryset = FreightRate.objects.all()
    serializer_class = FreightRateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )
    permission_classes_by_action = {
        'freight_rate_search_and_calculate': (IsAuthenticated, IsClientCompany, ),
    }
    filter_class = FreightRateFilterSet
    filter_backends = (filters.OrderingFilter, rest_framework.DjangoFilterBackend,)
    ordering_fields = ('shipping_mode', 'carrier', 'origin', 'destination', )

    def get_serializer_class(self):
        if self.action == 'list':
            return FreightRateListSerializer
        if self.action == 'retrieve':
            return FreightRateRetrieveSerializer
        if self.action in ('update', 'partial_update'):
            return FreightRateEditSerializer
        return self.serializer_class

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(company=user.companies.first())
        if self.action == 'list':
            return queryset.annotate(direction=Case(
                When(origin__code__startswith=MAIN_COUNTRY_CODE, then=Value('export')),
                default=Value('import'),
                output_field=CharField()
            ))
        return queryset

    @action(methods=['post'], detail=False, url_path='check-date')
    def check_date(self, request, *args, **kwargs):
        serializer = FreightRateCheckDatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        freight_rate = data.pop('freight_rate') if 'freight_rate' in data else None
        freight_rates = self.get_queryset().filter(**data).exclude(id=freight_rate)
        results = [[{
            key: (value.strftime('%m/%d/%Y') if isinstance(value, datetime) else value) for key, value in rate.items()
        } for rate in freight_rate.rates.values('container_type', 'start_date', 'expiration_date')]
            for freight_rate in freight_rates]
        return Response(data=results, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False, url_path='check-surcharge')
    def check_surcharge(self, request, *args, **kwargs):
        serializer = CheckRateDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        user = self.request.user
        port = Port.objects.get(id=data['origin'])
        direction = 'export' if port.code.startswith(MAIN_COUNTRY_CODE) else 'import'
        location = data['origin'] if direction == 'export' else data['destination']
        start_date = date_format(data['start_date'])
        expiration_date = date_format(data['expiration_date'])
        filter_fields = {
            'carrier': data['carrier'],
            'direction': direction,
            'location': location,
            'shipping_mode': data['shipping_mode'],
        }
        start_date_fields = {
            'start_date__gte': start_date,
            'start_date__lte': expiration_date,
        }
        end_date_fields = {
            'expiration_date__gte': start_date,
            'expiration_date__lte': expiration_date,
        }
        surcharge = Surcharge.objects.filter(
            Q(**filter_fields),
            Q(Q(**start_date_fields), Q(**end_date_fields), _connector='OR'),
            company=user.companies.first()
        ).order_by('start_date').first()
        data = {}
        if surcharge:
            data = SurchargeRetrieveSerializer(surcharge).data
        return Response(data=data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False, url_path='search')
    def freight_rate_search_and_calculate(self, request, *args, **kwargs):
        serializer = FreightRateSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        cargo_groups = data.get('cargo_groups')
        container_type_ids_list = [group.get('container_type') for group in cargo_groups if 'container_type' in group]
        date_from = date_format(data.get('date_from'))
        date_to = date_format(data.get('date_to'))
        freight_rates, shipping_mode = freight_rate_search(data)

        number_of_results = ClientPlatformSetting.objects.first().number_of_results
        freight_rates = freight_rates.order_by('transit_time').distinct()[:number_of_results]

        local_fees = request.user.companies.first().fees.filter(shipping_mode=shipping_mode)
        global_fees = GlobalFee.objects.filter(shipping_mode=shipping_mode)
        local_booking_fee = local_fees.filter(fee_type=GlobalFee.BOOKING, is_active=True).first()
        local_service_fee = local_fees.filter(fee_type=GlobalFee.SERVICE, is_active=True).first()
        booking_fee = local_booking_fee if local_booking_fee else \
            global_fees.filter(fee_type=GlobalFee.BOOKING, is_active=True).first()
        service_fee = local_service_fee if local_service_fee else \
            global_fees.filter(fee_type=GlobalFee.SERVICE, is_active=True).first()
        service_fee = service_fee.value if service_fee else 0
        results = []
        main_currency_code = Currency.objects.filter(is_main=True).first().code
        for freight_rate in freight_rates:
            totals = dict()
            totals['total_freight_rate'] = dict()
            totals['total_surcharge'] = dict()
            result = dict()
            result['freight_rate'] = FreightRateSearchListSerializer(freight_rate).data
            result['cargo_groups'] = []
            if shipping_mode.is_need_volume:
                rate = freight_rate.rates.first()
                exchange_rate = ExchangeRate.objects.filter(currency__code=rate.currency.code).first()
                for cargo_group in cargo_groups:
                    new_cargo_group = dict()
                    total_weight_per_pack, total_weight = wm_calculate(cargo_group, shipping_mode.shipping_type.title)

                    new_cargo_group['freight'] = calculate_freight_rate(totals,
                                                                        rate,
                                                                        booking_fee,
                                                                        main_currency_code,
                                                                        exchange_rate,
                                                                        total_weight_per_pack=total_weight_per_pack,
                                                                        total_weight=total_weight)

                    surcharge = rate.surcharges.filter(start_date__lte=date_from,
                                                       expiration_date__gte=date_to).first()
                    charges = surcharge.charges.all()
                    usage_fee = surcharge.usage_fees.filter(container_type=cargo_group.get('container_type')).first()
                    calculate_additional_surcharges(totals,
                                                    charges,
                                                    usage_fee,
                                                    cargo_group,
                                                    shipping_mode,
                                                    new_cargo_group,
                                                    total_weight_per_pack)
                    new_cargo_group['volume'] = cargo_group.get('volume')
                    container_type = cargo_group.get('container_type')
                    packaging_type = cargo_group.get('packaging_type')
                    new_cargo_group['cargo_type'] = ContainerType.objects.filter(id=container_type).first().code \
                        if container_type else PackagingType.objects.filter(id=packaging_type).first().description

                    result['cargo_groups'].append(new_cargo_group)
            else:
                rates = freight_rate.rates.all()
                for cargo_group in cargo_groups:
                    new_cargo_group = dict()
                    rate = rates.filter(container_type=cargo_group.get('container_type')).first()
                    exchange_rate = ExchangeRate.objects.filter(currency__code=rate.currency.code).first()

                    new_cargo_group['freight'] = calculate_freight_rate(totals,
                                                                        rate,
                                                                        booking_fee,
                                                                        main_currency_code,
                                                                        exchange_rate,
                                                                        volume=cargo_group.get('volume'))

                    surcharge = rate.surcharges.filter(start_date__lte=date_from,
                                                       expiration_date__gte=date_to).first()
                    charges = surcharge.charges.all()
                    usage_fee = surcharge.usage_fees.filter(container_type=cargo_group.get('container_type')).first()
                    calculate_additional_surcharges(totals,
                                                    charges,
                                                    usage_fee,
                                                    cargo_group,
                                                    shipping_mode,
                                                    new_cargo_group)
                    new_cargo_group['volume'] = cargo_group.get('volume')
                    container_type = cargo_group.get('container_type')
                    new_cargo_group['cargo_type'] = ContainerType.objects.filter(id=container_type).first().code

                    result['cargo_groups'].append(new_cargo_group)

            doc_fee = dict()
            filter_data = {}
            if shipping_mode.has_freight_containers:
                filter_data['container_type__id'] = container_type_ids_list[0]
            surcharge = freight_rate.rates.filter(**filter_data).first().surcharges.filter(
                start_date__lte=date_from,
                expiration_date__gte=date_to,
            ).first()
            charge = surcharge.charges.filter(additional_surcharge__is_document=True).first()
            doc_fee['currency'] = charge.currency.code
            doc_fee['cost'] = charge.charge
            doc_fee['subtotal'] = charge.charge
            result['doc_fee'] = doc_fee
            add_currency_value(totals, charge.currency.code, charge.charge)

            service_fee_dict = dict()
            service_fee_dict['currency'] = main_currency_code
            service_fee_dict['cost'] = service_fee
            service_fee_dict['subtotal'] = service_fee
            result['service_fee'] = service_fee_dict
            add_currency_value(totals, main_currency_code, service_fee)

            total_booking_fee = totals.pop('booking_fee')
            pay_to_book = service_fee + total_booking_fee
            total_freight_rate = totals.pop('total_freight_rate')
            total_surcharge = totals.pop('total_surcharge')
            result['total_freight_rate'] = total_freight_rate
            result['total_surcharge'] = total_surcharge
            result['totals'] = totals
            result['pay_to_book'] = {
                'service_fee': service_fee,
                'booking_fee': total_booking_fee,
                'pay_to_book': pay_to_book,
                'currency': main_currency_code,
            }

            results.append(result)

        return Response(data=results, status=status.HTTP_200_OK)


class RateViesSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Rate.objects.all()
    serializer_class = RateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(freight_rate__company=user.companies.first())


class WMCalculateView(generics.GenericAPIView):
    serializer_class = WMCalculateSerializer
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        total_per_pack, total = wm_calculate(data)
        results = {
            'total_per_pack': total_per_pack,
            'total': total,
        }
        return Response(data=results, status=status.HTTP_200_OK)


class QuoteViesSet(PermissionClassByActionMixin,
                   viewsets.ModelViewSet):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = (IsAuthenticated, )
    permission_classes_by_action = {
        'list': (IsAuthenticated, IsClientCompany,),
        'get_agent_quotes_list': (IsAuthenticated, IsAgentCompany,),
        'freight_rate_search': (IsAuthenticated, IsAgentCompany,),
    }
    filter_class = QuoteFilterSet
    filter_backends = (QuoteOrderingFilterBackend, rest_framework.DjangoFilterBackend,)

    def get_queryset(self):
        user = self.request.user
        company = user.companies.first()
        queryset = self.queryset
        if company.type == Company.CLIENT:
            queryset = self.queryset.filter(company=company)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        if self.action == 'get_agent_quotes_list':
            return QuoteAgentListOrRetrieveSerializer
        if self.action == 'retrieve':
            return QuoteAgentListOrRetrieveSerializer
        return self.serializer_class

    @action(methods=['get'], detail=False, url_path='agent-quotes-list')
    def get_agent_quotes_list(self, request, *args, **kwargs):
        user = request.user
        company = user.companies.first()

        queryset = self.get_queryset().exclude(statuses__status=Status.REJECTED,
                                               statuses__company=company)
        submitted_air = queryset.filter(shipping_mode__shipping_type__title='air',
                                        statuses__status=Status.SUBMITTED,
                                        freight_rates__company=company)
        submitted_sea = queryset.filter(shipping_mode__shipping_type__title='sea',
                                        statuses__status=Status.SUBMITTED,
                                        freight_rates__company=company)

        number_of_bids = ClientPlatformSetting.objects.first().number_of_bids
        queryset = queryset.annotate(bids_count=Count('statuses')).filter(bids_count__lt=number_of_bids)

        not_submitted_air = queryset.filter(shipping_mode__shipping_type__title='air').exclude(
            statuses__status=Status.SUBMITTED,
            freight_rates__company=company
        ).order_by('date_created')[:10]
        not_submitted_sea = queryset.filter(shipping_mode__shipping_type__title='sea').exclude(
            statuses__status=Status.SUBMITTED,
            freight_rates__company=company
        ).order_by('date_created')[:10]

        queryset = (submitted_air | submitted_sea | not_submitted_air | not_submitted_sea).order_by('date_created')
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='freight-rate-search')
    def freight_rate_search(self, request, *args, **kwargs):
        user = request.user
        serializer = FreightRateSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        freight_rates, _ = freight_rate_search(data, company=user.companies.first())
        freight_rate = freight_rates.first()
        data = FreightRateRetrieveSerializer(freight_rate)
        return Response(data)


class BookingViesSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (IsAuthenticated, )
