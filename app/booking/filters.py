from rest_framework import filters

import django_filters
from django.db.models import Q

from app.booking.models import FreightRate, Surcharge, Quote, Booking, TrackStatus
from app.core.models import Company


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


class BookingFilterSet(django_filters.FilterSet):
    shipping_type = django_filters.CharFilter(field_name='freight_rate__shipping_mode__shipping_type__title')
    route = django_filters.CharFilter(method='route_filter', label='Route filter')
    client = django_filters.CharFilter(field_name='client_contact_person__companies__name', lookup_expr='icontains')

    class Meta:
        model = Booking
        fields = (
            'shipping_type',
            'route',
            'client',
        )

    def route_filter(self, queryset, _, value):
        return queryset.filter(
            Q(freight_rate__origin__code__icontains=value) | Q(freight_rate__destination__code__icontains=value)
        ).distinct()


class BookingOrderingFilterBackend(filters.BaseFilterBackend):
    valid_ordering_fields = ('shipping_mode', 'client', 'shipment_date', 'status')

    def filter_queryset(self, request, queryset, view):

        ordering = request.query_params.get('ordering', 'date_from')
        if ordering.strip('-') in self.valid_ordering_fields:
            asc_or_desc = '-' if ordering.startswith('-') else ''
            if ordering.endswith('shipping_mode'):
                queryset = queryset.order_by(f'{asc_or_desc}freight_rate__shipping_mode__title', 'date_from')
            elif ordering.endswith('client'):
                queryset = queryset.order_by(f'{asc_or_desc}client_contact_person__companies__name', 'date_from')
            elif ordering.endswith('shipment_date'):
                queryset = queryset.order_by(f'{asc_or_desc}date_from')
            elif ordering.endswith('status'):
                queryset = queryset.order_by(f'{asc_or_desc}status', 'date_from')
            else:
                queryset = queryset.order_by(ordering)

        return queryset


class OperationFilterSet(django_filters.FilterSet):
    shipping_type = django_filters.CharFilter(field_name='freight_rate__shipping_mode__shipping_type__title')
    my_operations = django_filters.BooleanFilter(method='my_operations_filter', label='My Operations')
    aceid = django_filters.CharFilter(field_name='aceid', lookup_expr='icontains')
    carrier = django_filters.CharFilter(field_name='freight_rate__carrier__title', lookup_expr='icontains')
    status = django_filters.CharFilter(method='status_filter', label='Operation statuses')
    route = django_filters.CharFilter(method='route_filter', label='Route filter')

    class Meta:
        model = Booking
        fields = (
            'shipping_type',
            'my_operations',
            'aceid',
            'carrier',
            'route',
        )

    def route_filter(self, queryset, _, value):
        return queryset.filter(
            Q(freight_rate__origin__code__icontains=value) | Q(freight_rate__destination__code__icontains=value)
        ).distinct()

    def my_operations_filter(self, queryset, _, value):
        if value:
            user = self.request.user
            if user.get_company().type == Company.CLIENT:
                queryset = queryset.filter(client_contact_person=user)
            else:
                queryset = queryset.filter(agent_contact_person=user)
        return queryset

    def status_filter(self, queryset, _, value):
        if value == 'active':
            user = self.request.user
            if user.get_company().type == Company.CLIENT:
                queryset = queryset.filter(status__in=(
                    Booking.PENDING,
                    Booking.REQUEST_RECEIVED,
                    Booking.ACCEPTED,
                    Booking.CONFIRMED,
                ))
            else:
                queryset = queryset.filter(status__in=(Booking.ACCEPTED, Booking.CONFIRMED))
        elif value == 'completed':
            queryset = queryset.filter(status__in=(Booking.COMPLETED,))
        elif value == 'canceled':
            queryset = queryset.filter(status__in=(
                Booking.CANCELED_BY_AGENT,
                Booking.CANCELED_BY_CLIENT,
                Booking.CANCELED_BY_SYSTEM,
                Booking.REJECTED,
            ))
        return queryset


class OperationOrderingFilterBackend(filters.BaseFilterBackend):
    valid_ordering_fields = (
        'aceid',
        'route',
        'date',
        'carrier',
        'status',
        'agent',
        'shipping_mode',
        'payment_due_by',
    )

    def filter_queryset(self, request, queryset, view):

        ordering = request.query_params.get('ordering', 'date_from')
        if ordering.strip('-') in self.valid_ordering_fields:
            asc_or_desc = '-' if ordering.startswith('-') else ''
            if ordering.endswith('route'):
                queryset = queryset.order_by(f'{asc_or_desc}freight_rate__origin__code', 'date_from')
            elif ordering.endswith('date'):
                queryset = queryset.order_by(f'{asc_or_desc}shipment_details__date_of_departure', 'date_from')
            elif ordering.endswith('carrier'):
                queryset = queryset.order_by(f'{asc_or_desc}freight_rate__carrier__title', 'date_from')
            elif ordering.endswith('agent'):
                queryset = queryset.order_by(f'{asc_or_desc}agent_contact_person__first_name', 'date_from')
            elif ordering.endswith('shipping_mode'):
                queryset = queryset.order_by(f'{asc_or_desc}freight_rate__shipping_mode__title', 'date_from')
            else:
                queryset = queryset.order_by(ordering)

        return queryset


class TrackStatusFilterSet(django_filters.FilterSet):
    direction = django_filters.CharFilter(field_name='direction__title')
    departure_is_set = django_filters.BooleanFilter(field_name='show_after_departure')

    class Meta:
        model = TrackStatus
        fields = (
            'shipping_mode',
            'direction',
            'departure_is_set',
        )


class OperationBillingFilterSet(OperationFilterSet):
    date_from = django_filters.DateFilter(field_name='date_created', lookup_expr='gte', input_formats=['%d/%m/%Y'])
    date_to = django_filters.DateFilter(field_name='date_created', lookup_expr='lt', input_formats=['%d/%m/%Y'])

    class Meta(OperationFilterSet.Meta):
        model = Booking
        fields = OperationFilterSet.Meta.fields + (
            'date_from',
            'date_to',
        )

    def status_filter(self, queryset, _, value):
        if value == 'pending':
            queryset = queryset.filter(status=Booking.PENDING)
        if value == 'active':
            user = self.request.user
            if user.get_company().type == Company.CLIENT:
                queryset = queryset.filter(status__in=(
                    Booking.REQUEST_RECEIVED,
                    Booking.ACCEPTED,
                    Booking.CONFIRMED,
                ))
            else:
                queryset = queryset.filter(status=Booking.CONFIRMED)
        elif value == 'completed':
            queryset = queryset.filter(status__in=(Booking.COMPLETED,))
        return queryset
