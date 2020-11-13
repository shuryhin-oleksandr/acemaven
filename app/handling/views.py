from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework
from rest_framework.filters import SearchFilter

from django.db.models import BooleanField, Case, QuerySet, When, Q

from app.handling.filters import CarrierFilterSet, PortFilterSet
from app.handling.models import Carrier, Port, ShippingMode, ShippingType, Currency, PackagingType
from app.handling.serializers import CarrierSerializer, CurrencySerializer, PortSerializer, ShippingModeSerializer, \
    ShippingTypeSerializer, PackagingTypeBaseSerializer
from app.location.models import Country


main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


class CarrierViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = (IsAuthenticated, )
    filter_class = CarrierFilterSet
    filter_backends = (rest_framework.DjangoFilterBackend,)


class PortViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer
    permission_classes = (IsAuthenticated, )
    filter_class = PortFilterSet
    filter_backends = (SearchFilter, rest_framework.DjangoFilterBackend,)
    search_fields = ('code', 'name',)

    def get_queryset(self):
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        queryset = queryset.annotate(is_local=Case(
            When(code__startswith=MAIN_COUNTRY_CODE, then=True),
            default=False,
            output_field=BooleanField(),
        ))
        return queryset


class ShippingModeViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = ShippingMode.objects.all()
    serializer_class = ShippingModeSerializer
    permission_classes = (IsAuthenticated, )


class ShippingTypeViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = ShippingType.objects.all()
    serializer_class = ShippingTypeSerializer
    permission_classes = (IsAuthenticated, )


class PackagingTypeViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    queryset = PackagingType.objects.all()
    serializer_class = PackagingTypeBaseSerializer
    permission_classes = (IsAuthenticated, )


class CurrencyViewSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return Currency.objects.filter(Q(country__code=MAIN_COUNTRY_CODE) | (Q(is_active=True))).distinct()
