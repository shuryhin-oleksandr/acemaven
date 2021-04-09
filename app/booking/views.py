from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django_filters import rest_framework
from rest_framework import mixins, viewsets, filters, status, generics, views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import CharField, Case, When, Value, Q, Count, Min
from django.db.utils import ProgrammingError
from django.utils import timezone

from app.booking.filters import SurchargeFilterSet, FreightRateFilterSet, QuoteFilterSet, QuoteOrderingFilterBackend, \
    BookingFilterSet, BookingOrderingFilterBackend, OperationFilterSet, OperationOrderingFilterBackend, \
    TrackStatusFilterSet, OperationBillingFilterSet
from app.booking.mixins import FeeGetQuerysetMixin
from app.booking.models import Surcharge, UsageFee, Charge, FreightRate, Rate, Quote, Booking, Status, \
    ShipmentDetails, CancellationReason, CargoGroup, Track, TrackStatus, PaymentData, Transaction
from app.booking.serializers import SurchargeSerializer, SurchargeEditSerializer, SurchargeListSerializer, \
    SurchargeRetrieveSerializer, UsageFeeSerializer, ChargeSerializer, FreightRateListSerializer, \
    SurchargeCheckDatesSerializer, FreightRateEditSerializer, FreightRateSerializer, FreightRateRetrieveSerializer, \
    RateSerializer, CheckRateDateSerializer, FreightRateCheckDatesSerializer, WMCalculateSerializer, \
    FreightRateSearchSerializer, FreightRateSearchListSerializer, QuoteSerializer, BookingSerializer, \
    QuoteClientListOrRetrieveSerializer, QuoteAgentListSerializer, QuoteAgentRetrieveSerializer, \
    QuoteStatusBaseSerializer, CargoGroupSerializer, BookingListBaseSerializer, BookingRetrieveSerializer, \
    ShipmentDetailsBaseSerializer, OperationSerializer, OperationListBaseSerializer, OperationRetrieveSerializer, \
    OperationRetrieveClientSerializer, OperationRecalculateSerializer, TrackSerializer, TrackStatusSerializer, \
    TrackRetrieveSerializer, OperationBillingAgentListSerializer, OperationBillingClientListSerializer, \
    TrackWidgetListSerializer, OperationListClientSerializer
from app.booking.utils import date_format, wm_calculate, freight_rate_search, calculate_freight_rate_charges, \
    get_fees, surcharge_search, make_copy_of_surcharge, make_copy_of_freight_rate, \
    apply_operation_select_prefetch_related
from app.core.mixins import PermissionClassByActionMixin
from app.core.models import Company, BankAccount, Review
from app.core.permissions import IsMasterOrAgent, IsClientCompany, IsAgentCompany
from app.core.serializers import ReviewBaseSerializer
from app.handling.models import Port, Currency, ClientPlatformSetting
from app.location.models import Country
from app.websockets.models import Notification, Chat
from app.websockets.tasks import create_and_assign_notification, reassign_confirmed_operation_notifications, \
    delete_accepted_booking_notifications, send_email, create_chat_for_operation
from app.booking.tasks import change_charge
from config import settings
from app.core.util.get_jwt_token import get_jwt_token

try:
    MAIN_COUNTRY_CODE = Country.objects.filter(is_main=True).first().code
except (ProgrammingError, AttributeError):
    MAIN_COUNTRY_CODE = 'BR'


class SurchargeViesSet(viewsets.ModelViewSet):
    queryset = Surcharge.objects.all()
    serializer_class = SurchargeSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent,)
    filter_class = SurchargeFilterSet
    filter_backends = (filters.OrderingFilter, rest_framework.DjangoFilterBackend,)
    ordering_fields = ('shipping_mode', 'carrier', 'location', 'start_date', 'expiration_date',)

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
        return self.queryset.filter(
            company=user.get_company(),
            temporary=False,
            is_archived=False,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        new_surcharge_id = serializer.data.get('id')
        surcharge = Surcharge.objects.get(id=new_surcharge_id)
        data = SurchargeRetrieveSerializer(surcharge).data
        return Response(data=data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        data = request.data
        usage_fees = data.pop('usage_fees', [])
        charges = data.pop('charges', [])
        partial = kwargs.pop('partial', False)
        surcharge = self.get_object()
        surcharge, fees_map = make_copy_of_surcharge(
            surcharge,
            get_usage_fees_map=True,
            get_charges_map=True,
        )
        surcharge_serializer = self.get_serializer(surcharge, data=request.data, partial=partial)
        surcharge_serializer.is_valid(raise_exception=True)
        self.perform_update(surcharge_serializer)

        context = self.get_serializer_context()

        for usage_fee in usage_fees:
            old_usage_fee_id = usage_fee.pop('id')
            serializer = UsageFeeSerializer(
                fees_map['usage_fees'][old_usage_fee_id],
                data=usage_fee,
                partial=True,
                context=context,
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        for charge in charges:
            old_charge_id = charge.pop('id')
            serializer = ChargeSerializer(
                fees_map['charges'][old_charge_id],
                data=charge,
                partial=True,
                context=context,
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        if getattr(surcharge, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            surcharge._prefetched_objects_cache = {}

        return Response(SurchargeRetrieveSerializer(surcharge).data)

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
    permission_classes = (IsAuthenticated, IsMasterOrAgent,)


class ChargeViesSet(FeeGetQuerysetMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = Charge.objects.all()
    serializer_class = ChargeSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent,)


class FreightRateViesSet(PermissionClassByActionMixin,
                         viewsets.ModelViewSet):
    queryset = FreightRate.objects.all()
    serializer_class = FreightRateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent,)
    permission_classes_by_action = {
        'freight_rate_search_and_calculate': (IsAuthenticated, IsClientCompany,),
        'save_freight_rate': (IsAuthenticated, IsAgentCompany,),
    }
    filter_class = FreightRateFilterSet
    filter_backends = (filters.OrderingFilter, rest_framework.DjangoFilterBackend,)
    ordering_fields = ('shipping_mode', 'carrier', 'origin', 'destination',)

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
        temporary = True if self.action == 'save_freight_rate' else False
        queryset = self.queryset.filter(
            company=user.get_company(),
            temporary=temporary,
            is_archived=False,
        )
        if self.action == 'list':
            return queryset.annotate(direction=Case(
                When(origin__code__startswith=MAIN_COUNTRY_CODE, then=Value('export')),
                default=Value('import'),
                output_field=CharField()
            ))
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        new_freight_rate_id = serializer.data.get('id')
        freight_rate = FreightRate.objects.get(id=new_freight_rate_id)
        data = FreightRateRetrieveSerializer(freight_rate).data
        return Response(data=data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        data = request.data
        rates = data.pop('rates', [])
        partial = kwargs.pop('partial', False)
        freight_rate = self.get_object()
        freight_rate, fees_map = make_copy_of_freight_rate(
            freight_rate,
            get_rates_map=True,
        )
        freight_rate_serializer = self.get_serializer(freight_rate, data=request.data, partial=partial)
        freight_rate_serializer.is_valid(raise_exception=True)
        self.perform_update(freight_rate_serializer)

        context = self.get_serializer_context()

        for rate in rates:
            old_rate_id = rate.pop('id')
            serializer = RateSerializer(
                fees_map[old_rate_id],
                data=rate,
                partial=True,
                context=context,
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        if getattr(freight_rate_serializer, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            freight_rate_serializer._prefetched_objects_cache = {}

        return Response(FreightRateRetrieveSerializer(freight_rate).data)

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

    @action(methods=['post'], detail=True, url_path='save')
    def save_freight_rate(self, request, *args, **kwargs):
        user = request.user
        freight_rate = self.get_object()
        old_freight_rates = self.queryset.filter(company=user.get_company(),
                                                 shipping_mode=freight_rate.shipping_mode,
                                                 origin=freight_rate.origin,
                                                 destination=freight_rate.destination,
                                                 carrier=freight_rate.carrier,
                                                 temporary=False,
                                                 is_archived=False, )
        shipping_mode = freight_rate.shipping_mode

        rates = freight_rate.rates.all()
        if shipping_mode.has_freight_containers:
            new_not_empty_rates = rates.filter(start_date__isnull=False)
            for old_freight_rate in old_freight_rates:
                for new_rate in new_not_empty_rates:
                    if old_freight_rate.rates.filter(
                            Q(
                                Q(start_date__gt=new_rate.start_date, start_date__lte=new_rate.expiration_date),
                                Q(expiration_date__gte=new_rate.start_date,
                                  expiration_date__lt=new_rate.expiration_date),
                                Q(start_date__lte=new_rate.start_date, expiration_date__gte=new_rate.expiration_date),
                                Q(start_date__isnull=True),
                                _connector='OR',
                            ),
                            container_type=new_rate.container_type,
                    ).exists():
                        return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            new_rate = rates.first()
            for old_freight_rate in old_freight_rates:
                if old_freight_rate.rates.filter(
                        Q(
                            Q(start_date__gt=new_rate.start_date, start_date__lte=new_rate.expiration_date),
                            Q(expiration_date__gte=new_rate.start_date, expiration_date__lt=new_rate.expiration_date),
                            Q(start_date__lte=new_rate.start_date, expiration_date__gte=new_rate.expiration_date),
                            _connector='OR',
                        )
                ).exists():
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        freight_rate.temporary = False
        freight_rate.save()
        for rate in rates:
            rate.surcharges.filter(temporary=True).update(temporary=False)

        return Response(status=status.HTTP_200_OK)

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
            'start_date__lt': start_date,
            'expiration_date__gte': start_date,
        }
        mid_date_field = {
            'start_date__gte': start_date,
            'expiration_date__lte': expiration_date,
        }
        end_date_fields = {
            'start_date__lte': expiration_date,
            'expiration_date__gt': expiration_date,
        }
        surcharge = Surcharge.objects.filter(
            Q(**filter_fields),
            Q(Q(**start_date_fields), Q(**end_date_fields), Q(**mid_date_field), _connector='OR'),
            company=user.get_company(),
            temporary=False,
            is_archived=False,
        ).order_by('start_date').first()
        data = {}
        if surcharge:
            data = SurchargeRetrieveSerializer(surcharge).data
        return Response(data=data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False, url_path='search')
    def freight_rate_search_and_calculate(self, request, *args, **kwargs):
        company = request.user.get_company()
        if company.disabled:
            return Response(data=[], status=status.HTTP_200_OK)
        serializer = FreightRateSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        cargo_groups = data.get('cargo_groups')
        container_type_ids_list = [group.get('container_type') for group in cargo_groups if group.get('container_type')]
        date_from = date_format(data.get('date_from'))
        date_to = date_format(data.get('date_to'))
        freight_rates, shipping_mode = freight_rate_search(data)

        client_platform_settings = ClientPlatformSetting.load()
        number_of_results = client_platform_settings.number_of_results
        calculate_fees = client_platform_settings.enable_booking_fee_payment
        freight_rates = freight_rates.order_by('transit_time').distinct()[:number_of_results]

        booking_fee, service_fee = get_fees(company, shipping_mode)
        main_currency_code = Currency.objects.filter(is_main=True).first().code
        results = []

        for freight_rate in freight_rates:
            freight_rate_dict = FreightRateSearchListSerializer(freight_rate).data
            if container_type_ids_list:
                condition = {} if not shipping_mode.has_freight_containers else {
                    'container_type__id__in': container_type_ids_list}
                expiration_date = freight_rate.rates.filter(**condition).aggregate(
                    date=Min('expiration_date')).get('date').strftime('%d/%m/%Y')
                freight_rate_dict['expiration_date'] = expiration_date

            result = calculate_freight_rate_charges(freight_rate,
                                                    freight_rate_dict,
                                                    cargo_groups,
                                                    shipping_mode,
                                                    main_currency_code,
                                                    date_from,
                                                    date_to,
                                                    container_type_ids_list,
                                                    booking_fee=booking_fee,
                                                    service_fee=service_fee,
                                                    calculate_fees=calculate_fees, )

            results.append(result)

        return Response(data=results, status=status.HTTP_200_OK)


class RateViesSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Rate.objects.all()
    serializer_class = RateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent,)

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(freight_rate__company=user.get_company())


class WMCalculateView(generics.GenericAPIView):
    serializer_class = WMCalculateSerializer
    permission_classes = (IsAuthenticated,)

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
    permission_classes = (IsAuthenticated,)
    permission_classes_by_action = {
        'list': (IsAuthenticated, IsClientCompany,),
        'get_agent_quotes_list': (IsAuthenticated, IsAgentCompany,),
        'surcharge_search': (IsAuthenticated, IsAgentCompany,),
        'submit_quote': (IsAuthenticated, IsAgentCompany,),
        'reject_quote': (IsAuthenticated, IsAgentCompany,),
        'withdraw_quote': (IsAuthenticated, IsAgentCompany,),
        'archive_quote': (IsAuthenticated, IsClientCompany),
    }
    filter_class = QuoteFilterSet
    filter_backends = (QuoteOrderingFilterBackend, rest_framework.DjangoFilterBackend,)

    def get_queryset(self):
        user = self.request.user
        company = user.get_company()
        queryset = self.queryset.filter(is_archived=False)
        if company.type == Company.CLIENT:
            queryset = queryset.filter(company=company)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteClientListOrRetrieveSerializer
        if self.action == 'get_agent_quotes_list':
            return QuoteAgentListSerializer
        if self.action == 'retrieve':
            company = self.request.user.get_company()
            if company.type == Company.CLIENT:
                return QuoteClientListOrRetrieveSerializer
            return QuoteAgentRetrieveSerializer
        return self.serializer_class

    @action(methods=['get'], detail=False, url_path='agent-quotes-list')
    def get_agent_quotes_list(self, request, *args, **kwargs):
        user = request.user
        company = user.get_company()

        queryset = self.get_queryset().filter(is_active=True, company__disabled=False) \
            .exclude(statuses__status=Status.REJECTED,
                     statuses__company=company)
        submitted_air = queryset.filter(shipping_mode__shipping_type__title='air',
                                        statuses__status=Status.SUBMITTED,
                                        freight_rates__company=company)
        submitted_sea = queryset.filter(shipping_mode__shipping_type__title='sea',
                                        statuses__status=Status.SUBMITTED,
                                        freight_rates__company=company)

        number_of_bids = ClientPlatformSetting.load().number_of_bids
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

    @action(methods=['post'], detail=False, url_path='surcharge-search')
    def surcharge_search(self, request, *args, **kwargs):
        user = request.user
        serializer = FreightRateSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        surcharges = surcharge_search(data, user.get_company())
        surcharge = surcharges.first()
        data = SurchargeRetrieveSerializer(surcharge).data if surcharge else {}
        return Response(data)

    @transaction.atomic
    @action(methods=['post'], detail=True, url_path='submit')
    def submit_quote(self, request, *args, **kwargs):
        quote = self.get_object()
        number_of_bids = ClientPlatformSetting.load().number_of_bids
        if quote.statuses.filter(status=Status.SUBMITTED).count() < number_of_bids:
            try:
                with transaction.atomic():
                    data = request.data
                    data['quote'] = quote.id
                    data['status'] = Status.SUBMITTED

                    freight_rate = FreightRate.objects.filter(id=data.get('freight_rate')).first()
                    freight_rate_dict = FreightRateSearchListSerializer(freight_rate).data
                    cargo_groups = CargoGroupSerializer(quote.quote_cargo_groups, many=True).data
                    container_type_ids_list = [
                        group.get('container_type') for group in cargo_groups if group.get('container_type')
                    ]
                    main_currency_code = Currency.objects.filter(is_main=True).first().code

                    if container_type_ids_list:
                        condition = {} if not freight_rate.shipping_mode.has_freight_containers else {
                            'container_type__id__in': container_type_ids_list}
                        expiration_date = freight_rate.rates.filter(**condition).aggregate(
                            date=Min('expiration_date')).get('date').strftime('%d/%m/%Y')
                        freight_rate_dict['expiration_date'] = expiration_date

                    result = calculate_freight_rate_charges(freight_rate,
                                                            freight_rate_dict,
                                                            cargo_groups,
                                                            quote.shipping_mode,
                                                            main_currency_code,
                                                            quote.date_from,
                                                            quote.date_to,
                                                            container_type_ids_list, )
                    data['charges'] = result

                    serializer = QuoteStatusBaseSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    headers = self.get_success_headers(serializer.data)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

            except Exception as error:
                return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'error': 'Quote has reached the offers limit.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, url_path='reject')
    def reject_quote(self, request, *args, **kwargs):
        user = request.user
        quote = self.get_object()
        data = request.data
        data['quote'] = quote.id
        data['status'] = Status.REJECTED
        data['company'] = user.get_company().id
        serializer = QuoteStatusBaseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['post'], detail=True, url_path='withdraw')
    def withdraw_quote(self, request, *args, **kwargs):
        user = request.user
        quote = self.get_object()
        quote_status = quote.statuses.filter(freight_rate__company=user.get_company()).first()
        quote_status.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='archive')
    def archive_quote(self, request, *args, **kwargs):
        quote = self.get_object()
        quote.is_archived = True
        quote.save()
        return Response(status=status.HTTP_200_OK)


class BookingViesSet(PermissionClassByActionMixin,
                     viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (IsAuthenticated,)
    permission_classes_by_action = {
        'create': (IsAuthenticated, IsClientCompany,),
        'update': (IsAuthenticated, IsClientCompany,),
        'partial_update': (IsAuthenticated, IsClientCompany,),
        'assign_booking_to_agent': (IsAuthenticated, IsAgentCompany, IsMasterOrAgent,),
        'reject_booking': (IsAuthenticated, IsAgentCompany,),
    }
    filter_class = BookingFilterSet
    filter_backends = (BookingOrderingFilterBackend, rest_framework.DjangoFilterBackend,)

    def get_queryset(self):
        company = self.request.user.get_company()
        queryset = self.queryset.exclude(status=Booking.DISCARDED)
        if self.action in ('update', 'partial_update'):
            return queryset.filter(
                is_assigned=False,
                status__in=(Booking.PENDING, Booking.REQUEST_RECEIVED),
            )
        if self.action != 'assign_booking_to_agent':
            queryset = queryset.filter(
                is_assigned=False,
                status=Booking.REQUEST_RECEIVED
            )
        return queryset.filter(
            original_booking__isnull=True,
            freight_rate__company=company,
            is_paid=True
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListBaseSerializer
        if self.action == 'retrieve':
            return BookingRetrieveSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        new_booking_id = serializer.data.get('id')
        booking = Booking.objects.get(id=new_booking_id)
        data = BookingRetrieveSerializer(booking).data
        return Response(data=data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        company = self.request.user.get_company()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
        cargo_groups = data.pop('cargo_groups', {})
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        for cargo_group in cargo_groups:
            if 'id' in cargo_group:
                cargo_group_serializer = CargoGroupSerializer(
                    CargoGroup.objects.filter(id=cargo_group.get('id')).first(),
                    data=cargo_group,
                    partial=True,
                )
                cargo_group_serializer.is_valid(raise_exception=True)
                self.perform_update(cargo_group_serializer)
            else:
                cargo_group['booking'] = instance.id
                cargo_group_serializer = CargoGroupSerializer(data=cargo_group)
                cargo_group_serializer.is_valid(raise_exception=True)
                self.perform_create(cargo_group_serializer)

        freight_rate_dict = FreightRateSearchListSerializer(instance.freight_rate).data
        main_currency_code = Currency.objects.filter(is_main=True).first().code
        container_type_ids_list = [
            group.get('container_type') for group in cargo_groups if group.get('container_type')
        ]
        booking_fee, service_fee = get_fees(company, instance.freight_rate.shipping_mode)
        calculate_fees = ClientPlatformSetting.load().enable_booking_fee_payment
        try:
            if container_type_ids_list:
                condition = {} if not instance.freight_rate.shipping_mode.has_freight_containers else {
                    'container_type__id__in': container_type_ids_list}
                expiration_date = instance.freight_rate.rates.filter(**condition).aggregate(
                    date=Min('expiration_date')).get('date').strftime('%d/%m/%Y')
                freight_rate_dict['expiration_date'] = expiration_date

            kwargs = {'freight_rate': instance.freight_rate,
                      'freight_rate_dict': freight_rate_dict,
                      'cargo_groups': cargo_groups,
                      'shipping_mode': instance.freight_rate.shipping_mode,
                      'main_currency_code': main_currency_code,
                      'date_from': instance.date_from,
                      'date_to': instance.date_to,
                      'container_type_ids_list': container_type_ids_list,
                      'number_of_documents': instance.number_of_documents, }

            if not instance.is_paid:
                kwargs.update(booking_fee=booking_fee, service_fee=service_fee, calculate_fees=calculate_fees)
            new_charges = calculate_freight_rate_charges(**kwargs)

            try:
                with transaction.atomic():
                    instance.charges = new_charges
                    instance.save()

                    if not instance.is_paid:
                        bank_account = BankAccount.objects.filter(is_default=True, is_platforms=True).first()
                        pix_settings = bank_account.pix_api
                        txid = instance.transactions.values_list('txid', flat=True).first()
                        new_charge = new_charges.get('pay_to_book').get('pay_to_book')
                        instance.transactions.filter(booking=instance.id, status=Transaction.OPENED).update(charge=new_charge)
                        change_charge.delay(base_url=pix_settings.base_url, new_amount=new_charge,
                                            developer_key=pix_settings.developer_key, txid=txid,
                                            is_prod=pix_settings.is_prod, booking_id=instance.id,
                                            token_uri=pix_settings.token_uri, client_id=pix_settings.client_id,
                                            client_secret=pix_settings.client_secret, basic_token=pix_settings.basic_token,)
            except ValueError:
                return Response(
                    data={'error': 'could not change charge because of error.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except AttributeError:
            return Response(
                data={'error': 'date_from or date_to mismatch with surcharges or freight rate dates.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='assign')
    def assign_booking_to_agent(self, request, *args, **kwargs):
        booking = self.get_object()
        old_agent_contact_person = booking.agent_contact_person
        data = request.data
        assigned_user = get_user_model().objects.filter(id=data.get('user')).first()
        booking.agent_contact_person = assigned_user
        if booking.status == Booking.REQUEST_RECEIVED:
            booking.is_assigned = True
            booking.status = Booking.ACCEPTED
        now_date = timezone.localtime().date()
        booking.date_accepted_by_agent = now_date
        booking.save()

        if hasattr(booking, 'chat'):
            chat = booking.chat
            old_user_chat_permissions = old_agent_contact_person.chat_permissions.filter(chat=chat).first()
            old_user_chat_permissions.has_perm_to_write = False
            old_user_chat_permissions.save()
            if new_user_existing_chat_permissions := assigned_user.chat_permissions.filter(chat=chat).first():
                new_user_existing_chat_permissions.has_perm_to_write = True
                new_user_existing_chat_permissions.save()
            else:
                chat.users.add(assigned_user)

        if request.user != assigned_user:
            message_body = f'{request.user.get_full_name()} has assigned an operation to you. Operation [{booking.aceid}].'
            create_and_assign_notification.delay(
                Notification.REQUESTS,
                f'{request.user.get_full_name()} has assigned an operation to you. Operation [{booking.aceid}].',
                [assigned_user.id, ],
                Notification.OPERATION,
                object_id=booking.id,
            )
            send_email.delay(message_body,
                             [assigned_user.email], object_id=f'{settings.DOMAIN_ADDRESS}booking/{booking.id}')

        delete_accepted_booking_notifications.delay(booking.id)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='reject')
    def reject_booking(self, request, *args, **kwargs):
        booking = self.get_object()
        data = request.data
        data['agent_contact_person'] = request.user
        data['booking'] = booking
        CancellationReason.objects.create(**data)
        booking.status = Booking.REJECTED
        booking.save()
        return Response(status=status.HTTP_200_OK)


class OperationViewSet(PermissionClassByActionMixin,
                       viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = OperationSerializer
    permission_classes = (IsAuthenticated,)
    permission_classes_by_action = {
        'complete_operation': (IsAuthenticated, IsAgentCompany,),
        'leave_review': (IsAuthenticated, IsClientCompany,),
    }
    filter_class = OperationFilterSet
    filter_backends = (OperationOrderingFilterBackend, rest_framework.DjangoFilterBackend,)

    def get_queryset(self):
        company = self.request.user.get_company()
        queryset = self.queryset.filter(original_booking__isnull=True).exclude(status=Booking.DISCARDED)
        if company.type == Company.CLIENT:
            queryset = queryset.filter(client_contact_person__companies=company)
        else:
            queryset = queryset.exclude(
                status__in=(Booking.REQUEST_RECEIVED, Booking.PENDING, Booking.REJECTED)
            ).filter(
                freight_rate__company=company,
                is_assigned=True,
                is_paid=True,
            )
        return apply_operation_select_prefetch_related(queryset)

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.user.get_company().type == Company.CLIENT:
                return OperationListClientSerializer
            return OperationListBaseSerializer
        if self.action == 'retrieve':
            if self.request.user.get_company().type == Company.CLIENT:
                return OperationRetrieveClientSerializer
            return OperationRetrieveSerializer
        if self.action == 'leave_review':
            return ReviewBaseSerializer
        return self.serializer_class

    @action(methods=['post'], detail=True, url_path='cancel')
    def cancel_operation(self, request, *args, **kwargs):
        operation = self.get_object()
        if request.user.get_company().type == Company.CLIENT:
            operation.status = Booking.CANCELED_BY_CLIENT
        else:
            data = request.data
            data['agent_contact_person'] = request.user
            data['booking'] = operation
            CancellationReason.objects.create(**data)
            operation.status = Booking.CANCELED_BY_AGENT
        operation.save()
        operation.change_requests.all().delete()
        return Response(status=status.HTTP_200_OK)

    @transaction.atomic
    @action(methods=['post'], detail=True, url_path='confirm_change_request')
    def confirm_change_request(self, request, *args, **kwargs):
        operation = self.get_object()
        operation_id = operation.id
        change_request = operation.change_requests.first()

        if Chat.objects.filter(id=operation_id):
            chat = operation.chat
            chat.operation = change_request
            chat.save()
        # else:
        #     create_chat_for_operation.delay(change_request.id)
        #     chat = operation.chat
        #     chat.operation = change_request
        #     chat.save()

        operation.shipment_details.update(booking=change_request)
        operation.transactions.update(booking=change_request)
        operation.delete()

        change_request.change_request_status = Booking.CHANGE_CONFIRMED
        change_request.original_booking = None
        change_request.save()

        message_body = f'The Agent has confirmed your changes in the shipment {change_request.aceid} ' \
                       f'from {change_request.freight_rate.origin} to {change_request.freight_rate.destination}.'
        create_and_assign_notification.delay(
            Notification.OPERATIONS,
            f'The Agent has confirmed your changes in the shipment {change_request.aceid} '
            f'from {change_request.freight_rate.origin} to {change_request.freight_rate.destination}.',
            [change_request.client_contact_person_id, ],
            Notification.OPERATION,
            object_id=change_request.id,
        )

        reassign_confirmed_operation_notifications.delay(
            operation_id,
            change_request.id,
        )
        client_emails = [change_request.client_contact_person.email, ]
        send_email.delay(message_body, client_emails,
                         object_id=f'{settings.DOMAIN_ADDRESS}change_request/{change_request.id}')
        return Response(data={'id': change_request.id}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='cancel_change_request')
    def cancel_change_request(self, request, *args, **kwargs):
        operation = self.get_object()
        change_requests = operation.change_requests.all()
        change_requests.delete()
        operation.change_request_status = None
        operation.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='complete')
    def complete_operation(self, request, *args, **kwargs):
        operation = self.get_object()
        operation.status = Booking.COMPLETED
        operation.save()
        operation.change_requests.all().delete()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='recalculate')
    def recalculate_charges(self, request, *args, **kwargs):
        operation = self.get_object()
        serializer = OperationRecalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        freight_rate_dict = FreightRateSearchListSerializer(operation.freight_rate).data
        cargo_groups = data.get('cargo_groups')
        container_type_ids_list = [group.get('container_type') for group in cargo_groups if group.get('container_type')]
        main_currency_code = Currency.objects.filter(is_main=True).first().code
        number_of_documents = data.get('number_of_documents')
        if container_type_ids_list:
            condition = {} if not operation.freight_rate.shipping_mode.has_freight_containers else {
                'container_type__id__in': container_type_ids_list}
            expiration_date = operation.freight_rate.rates.filter(**condition).aggregate(
                date=Min('expiration_date')).get('date').strftime('%d/%m/%Y')
            freight_rate_dict['expiration_date'] = expiration_date
        result = calculate_freight_rate_charges(operation.freight_rate,
                                                freight_rate_dict,
                                                cargo_groups,
                                                operation.freight_rate.shipping_mode,
                                                main_currency_code,
                                                operation.date_from,
                                                operation.date_to,
                                                container_type_ids_list,
                                                number_of_documents=number_of_documents)

        return Response(data=result, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='review')
    def leave_review(self, request, *args, **kwargs):
        operation = self.get_object()
        request.data['operation'] = operation
        request.data['reviewer'] = request.user
        Review.objects.create(**request.data)
        request.data['operation'] = operation.id
        request.data['reviewer'] = request.user.id
        return Response(request.data, status=status.HTTP_201_CREATED)


class OperationBillingViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    queryset = Booking.objects.all()
    serializer_class = OperationBillingAgentListSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent,)
    filter_class = OperationBillingFilterSet
    filter_backends = (OperationOrderingFilterBackend, rest_framework.DjangoFilterBackend,)

    def get_queryset(self):
        company = self.request.user.get_company()
        queryset = self.queryset.filter(original_booking__isnull=True)
        if company.type == Company.CLIENT:
            queryset = queryset.filter(
                client_contact_person__companies=company,
                status__in=(
                    Booking.PENDING,
                    Booking.REQUEST_RECEIVED,
                    Booking.ACCEPTED,
                    Booking.CONFIRMED,
                    Booking.COMPLETED,
                ),
            )
        else:
            queryset = queryset.filter(
                freight_rate__company=company,
                status__in=(
                    Booking.CONFIRMED,
                    Booking.COMPLETED,
                ),
            )
        return queryset

    def get_serializer_class(self):
        company = self.request.user.get_company()
        if company.type == Company.CLIENT:
            return OperationBillingClientListSerializer
        return self.serializer_class


class StatusViesSet(mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = Status.objects.all()
    serializer_class = QuoteStatusBaseSerializer
    permission_classes = (IsAuthenticated,)


class ShipmentDetailsViesSet(viewsets.ModelViewSet):
    queryset = ShipmentDetails.objects.all()
    serializer_class = ShipmentDetailsBaseSerializer
    permission_classes = (IsAuthenticated,)


class TrackView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        data = request.data
        booking_number = data.get('airWaybillNumber')
        booking = Booking.objects.filter(shipment_details__booking_number=booking_number).first()
        if booking:
            direction = 'export' if booking.freight_rate.origin.code.startswith(MAIN_COUNTRY_CODE) else 'import'
            shipment_details = booking.shipment_details.first()
            origin_and_destination = data.get('originAndDestination')
            event = data.get('events')[0]
            destination = event.get('destination', '')
            origin = event.get('origin', '')
            time_of_event = datetime.strptime(event.get('timeOfEvent'), '%Y-%m-%dT%H:%M:%S')

            if event.get('type') == 'departed' and origin == origin_and_destination.get('origin'):
                shipment_details.actual_date_of_departure = time_of_event
                shipment_details.save()

                if direction == 'import':
                    message_body = f'The shipment {booking.aceid} has departed from {booking.freight_rate.origin}.'
                    create_and_assign_notification.delay(
                        Notification.OPERATIONS_IMPORT,
                        message_body,
                        [booking.agent_contact_person_id, booking.client_contact_person_id, ],
                        Notification.OPERATION,
                        object_id=booking.id,
                    )
                    emails = [booking.agent_contact_person.email, booking.client_contact_person.email, ]
                    send_email.delay(message_body, emails,
                                     object_id=f'{settings.DOMAIN_ADDRESS}shipment_departed/{booking.id}')

            if event.get('type') == 'arrived' and destination == origin_and_destination.get('destination'):
                shipment_details.actual_date_of_arrival = time_of_event
                shipment_details.save()

                if direction == 'export':
                    message_body = f'The shipment {booking.aceid} has arrived at {booking.freight_rate.destination}.'
                    create_and_assign_notification.delay(
                        Notification.OPERATIONS_EXPORT,
                        message_body,
                        [booking.agent_contact_person_id, booking.client_contact_person_id, ],
                        Notification.OPERATION,
                        object_id=booking.id,
                    )
                    emails = [booking.agent_contact_person.email, booking.client_contact_person.email, ]
                    send_email.delay(message_body, emails,
                                     object_id=f'{settings.DOMAIN_ADDRESS}shipment_arrived/{booking.id}')

        try:
            Track.objects.create(data=data, booking=booking)
        except Exception:
            Track.objects.create(data=str(data), booking=booking)
        return Response(status=status.HTTP_201_CREATED)


class PixApiView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            PaymentData.objects.create(data=data)
        except Exception:
            PaymentData.objects.create(data=str(data))
        return Response(status=status.HTTP_201_CREATED)


class TrackViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'get_widget_latest_tracking':
            return TrackWidgetListSerializer
        return self.serializer_class

    def perform_destroy(self, instance):
        shipment_details = instance.booking.shipment_details.first()
        track_status = instance.status
        if track_status.auto_add_on_actual_date_of_departure:
            shipment_details.actual_date_of_departure = None
        elif track_status.auto_add_on_actual_date_of_arrival:
            shipment_details.actual_date_of_arrival = None
        shipment_details.save()

        instance.delete()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        new_track_id = serializer.data.get('id')
        track = Track.objects.get(id=new_track_id)
        data = TrackRetrieveSerializer(track).data
        return Response(data=data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['get'], detail=False, url_path='widget')
    def get_widget_latest_tracking(self, request, *args, **kwargs):
        company = request.user.get_company()
        queryset = self.get_queryset().filter(booking__client_contact_person__companies=company)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TrackStatusViewSet(mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = TrackStatus.objects.all()
    serializer_class = TrackStatusSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = TrackStatusFilterSet
    filter_backends = (rest_framework.DjangoFilterBackend,)


class IndexView(TemplateView):
    template_name = "booking/index.js"
    content_type = "application/javascript"


@method_decorator(login_required, name='dispatch')
class OperationChatView(TemplateView):
    template_name = "booking/index.html"
    model = Chat

    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        chat_id = self.kwargs['chat_id']
        operation = self.kwargs['booking']
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "chat_id": chat_id,
                "token": get_jwt_token(user),
            }
        )
        return ctx
