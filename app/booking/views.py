from datetime import datetime

from django_filters import rest_framework
from rest_framework import mixins, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.conf import settings
from django.db.models import CharField, Case, When, Value, Q

from app.core.permissions import IsMasterOrAgent
from app.booking.filters import SurchargeFilterSet, FreightRateFilterSet
from app.booking.models import Surcharge, UsageFee, Charge, FreightRate, Rate
from app.booking.serializers import SurchargeSerializer, SurchargeEditSerializer, SurchargeListSerializer, \
    SurchargeRetrieveSerializer, UsageFeeSerializer, ChargeSerializer, FreightRateListSerializer, \
    SurchargeCheckDatesSerializer, FreightRateEditSerializer, FreightRateSerializer, FreightRateRetrieveSerializer, \
    RateSerializer, CheckRateDateSerializer, FreightRateCheckDatesSerializer
from app.booking.utils import date_format
from app.handling.models import Port


COUNTRY_CODE = settings.COUNTRY_OF_ORIGIN_CODE


class FeeGetQuerysetMixin:
    """
    Class, that provides custom get_queryset() method,
    returns objects connected only to users company.
    """

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(surcharge__company=user.companies.first())


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


class FreightRateViesSet(viewsets.ModelViewSet):
    queryset = FreightRate.objects.all()
    serializer_class = FreightRateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )
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
                When(origin__code__startswith=COUNTRY_CODE, then=Value('export')),
                default=Value('import'),
                output_field=CharField()
            ))
        return queryset

    @action(methods=['post'], detail=False, url_path='check-date')
    def check_date(self, request, *args, **kwargs):
        serializer = FreightRateCheckDatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        freight_rates = self.get_queryset().filter(**data).order_by('rates__start_date')
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
        direction = 'export' if port.code.startswith(COUNTRY_CODE) else 'import'
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


class RateViesSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Rate.objects.all()
    serializer_class = RateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(freight_rate__company=user.companies.first())
