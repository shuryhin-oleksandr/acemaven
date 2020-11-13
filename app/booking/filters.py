from rest_framework import filters

import django_filters
from django.db.models import Q

from app.booking.models import FreightRate, Surcharge, Quote


class SurchargeFilterSet(django_filters.FilterSet):
    shipping_type = django_filters.CharFilter(field_name='shipping_mode__shipping_type__title')
    shipping_mode = django_filters.CharFilter(field_name='shipping_mode__title', lookup_expr='icontains')
    carrier = django_filters.CharFilter(field_name='carrier__title', lookup_expr='icontains')
    location = django_filters.CharFilter(field_name='location__code', lookup_expr='icontains')

    class Meta:
        model = Surcharge
        fields = (
            'direction',
            'shipping_type',
            'shipping_mode',
            'carrier',
            'location',
            'start_date',
            'expiration_date',
        )


class FreightRateFilterSet(django_filters.FilterSet):
    direction = django_filters.CharFilter(label='Import or Export')
    shipping_type = django_filters.CharFilter(field_name='shipping_mode__shipping_type__title')
    shipping_mode = django_filters.CharFilter(field_name='shipping_mode__title', lookup_expr='icontains')
    carrier = django_filters.CharFilter(field_name='carrier__title', lookup_expr='icontains')
    origin = django_filters.CharFilter(field_name='origin__code', lookup_expr='icontains')
    destination = django_filters.CharFilter(field_name='destination__code', lookup_expr='icontains')

    class Meta:
        model = FreightRate
        fields = (
            'direction',
            'shipping_type',
            'shipping_mode',
            'carrier',
            'origin',
            'destination',
        )


class QuoteFilterSet(django_filters.FilterSet):
    shipping_type = django_filters.CharFilter(field_name='shipping_mode__shipping_type__title')
    shipping_mode = django_filters.CharFilter(field_name='shipping_mode__title', lookup_expr='icontains')
    origin = django_filters.CharFilter(field_name='origin__code', lookup_expr='icontains')
    destination = django_filters.CharFilter(field_name='destination__code', lookup_expr='icontains')
    route = django_filters.CharFilter(method='route_filter', label='Route filter')

    class Meta:
        model = Quote
        fields = (
            'shipping_type',
            'shipping_mode',
            'origin',
            'destination',
            'route',
        )

    def route_filter(self, queryset, _, value):
        return queryset.filter(Q(origin__code__icontains=value) | Q(destination__code__icontains=value))


class QuoteOrderingFilterBackend(filters.BaseFilterBackend):
    valid_ordering_fields = ('shipping_mode', 'origin', 'destination', 'date_from', 'route', 'status', 'shipment_date',)

    def filter_queryset(self, request, queryset, view):

        ordering = request.query_params.get('ordering', 'date_from')
        if ordering.strip('-') in self.valid_ordering_fields:
            asc_or_desc = '-' if ordering.startswith('-') else ''
            if ordering.endswith('shipping_mode'):
                queryset = queryset.order_by(f'{asc_or_desc}shipping_mode__title', 'date_from')
            elif ordering.endswith('route'):
                queryset = queryset.order_by(f'{asc_or_desc}origin__code', 'date_from')
            elif ordering.endswith('status'):
                queryset = queryset.order_by(f'{asc_or_desc}is_active', 'date_from')
            elif ordering.endswith('shipment_date'):
                queryset = queryset.order_by(f'{asc_or_desc}date_from')
            else:
                queryset = queryset.order_by(ordering)

        return queryset
