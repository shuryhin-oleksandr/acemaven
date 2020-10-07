import django_filters

from app.booking.models import Surcharge


class SurchargeFilterSet(django_filters.FilterSet):
    shipping_type = django_filters.CharFilter(field_name='shipping_mode__shipping_type__title')
    shipping_mode = django_filters.CharFilter(field_name='shipping_mode__title', lookup_expr='icontains')
    carrier = django_filters.CharFilter(field_name='carrier__title', lookup_expr='icontains')
    location = django_filters.CharFilter(field_name='port__code', lookup_expr='icontains')

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
