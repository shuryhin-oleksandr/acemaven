from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from app.core.models import SignUpRequest
from app.core.serializers import SignUpRequestSerializer


class SignUpRequestViewSet(mixins.CreateModelMixin,
                           viewsets.GenericViewSet):
    queryset = SignUpRequest.objects.all()
    serializer_class = SignUpRequestSerializer
    permission_classes = (IsAuthenticated,)
