from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from app.core.permissions import IsMasterOrAgent
from app.booking.models import Surcharge, UsageFee, Charge
from app.booking.serializers import SurchargeSerializer, SurchargeEditSerializer, SurchargeListSerializer, \
    SurchargeRetrieveSerializer, UsageFeeSerializer, ChargeSerializer


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
