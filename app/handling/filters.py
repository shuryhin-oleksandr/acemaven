import django_filters

from app.handling.models import Carrier, Port


class CarrierFilterSet(django_filters.FilterSet):
    shipping_type = django_filters.CharFilter(field_name='shipping_type__title')

    class Meta:
        model = Carrier
        fields = (
            'shipping_type',
        )


class PortFilterSet(django_filters.FilterSet):
    is_local = django_filters.BooleanFilter(label='Is local')
    shipping_type = django_filters.CharFilter(method='shipping_type_filter', label='Shipping type')

    class Meta:
        model = Port
        fields = (
            'is_local',
            'shipping_type',
        )

    def shipping_type_filter(self, queryset, _, value):
        filter_fields = {
            'sea': {
                'has_seaport': True,
            },
            'air': {
                'has_airport': True,
            },
        }
        return queryset.filter(**filter_fields.get(value, {}))
