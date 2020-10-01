from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework
from rest_framework.filters import SearchFilter

from django.conf import settings
from django.db.models import BooleanField, Case, QuerySet, When


from app.handling.filters import CarrierFilterSet, PortFilterSet
from app.handling.models import Carrier, Port
from app.handling.serializers import CarrierSerializer, PortSerializer


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
            When(code__startswith=settings.COUNTRY_OF_ORIGIN_CODE, then=True),
            default=False,
            output_field=BooleanField(),
        ))
        return queryset
