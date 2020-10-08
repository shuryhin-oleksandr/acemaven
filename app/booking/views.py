from django_filters import rest_framework
from rest_framework import mixins, viewsets, filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.core.permissions import IsMasterOrAgent
from app.booking.filters import SurchargeFilterSet
from app.booking.models import Surcharge, UsageFee, Charge, FreightRate, Rate
from app.booking.serializers import SurchargeSerializer, SurchargeEditSerializer, SurchargeListSerializer, \
    SurchargeRetrieveSerializer, UsageFeeSerializer, ChargeSerializer, FreightRateListSerializer, \
    SurchargeCheckDatesSerializer


class FeeGetQuerysetMixin:
    """
    Class, that provides custom get_queryset() method,
    returns objects connected only to users company.
    """

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(surcharge__company=user.companies.first())


class RateSurchargeGetQuerysetMixin:
    """
    Class, that provides custom get_queryset() method,
    returns objects connected only to users company.
    """

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(company=user.companies.first())


class SurchargeViesSet(RateSurchargeGetQuerysetMixin,
                       viewsets.ModelViewSet):
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


class CheckDateView(generics.GenericAPIView):
    queryset = Surcharge.objects.all()
    serializer_class = SurchargeCheckDatesSerializer
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        dates = self.get_queryset().filter(**data).order_by('start_date').values('start_date', 'expiration_date')
        results = [{key: value.strftime('%m/%d/%Y') for key, value in item.items()} for item in dates]
        return Response(data=results, status=status.HTTP_201_CREATED)


class FreightRateViesSet(RateSurchargeGetQuerysetMixin,
                         viewsets.ModelViewSet):
    queryset = FreightRate.objects.all()
    # serializer_class = FreightRateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )

    def get_serializer_class(self):
        if self.action == 'list':
            return FreightRateListSerializer
        if self.action == 'retrieve':
            return SurchargeRetrieveSerializer
        if self.action in ('update', 'partial_update'):
            return SurchargeEditSerializer
        return self.serializer_class


class RateViesSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Rate.objects.all()
    # serializer_class = RateSerializer
    permission_classes = (IsAuthenticated, IsMasterOrAgent, )

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(freight_rate__company=user.companies.first())

