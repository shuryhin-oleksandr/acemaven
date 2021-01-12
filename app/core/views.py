from rest_framework import generics, mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from django.contrib.auth import get_user_model, authenticate

from app.core.mixins import PermissionClassByActionMixin, CheckTokenMixin, CreateMixin
from app.core.models import BankAccount, Company, SignUpRequest, Shipper
from app.core.permissions import IsMaster, IsMasterOrBilling, IsAgentCompany, IsClientCompany
from app.core.serializers import CompanySerializer, SignUpRequestSerializer, UserBaseSerializer, UserCreateSerializer, \
    UserSignUpSerializer, BankAccountSerializer, UserMasterSerializer, UserSerializer, SelectChoiceSerializer, \
    UserBaseSerializerWithPhoto, CompanyReviewSerializer, ShipperSerializer
from app.core.utils import choice_to_value_name
from app.booking.models import CargoGroup, CancellationReason
from app.handling.models import ReleaseType, PackagingType, ContainerType


class BankAccountViewSet(PermissionClassByActionMixin,
                         CreateMixin,
                         viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = (IsAuthenticated, )
    permission_classes_by_action = {
        'create': [IsAuthenticated, IsMasterOrBilling, ],
        'destroy': [IsAuthenticated, IsMasterOrBilling, ],
        'update': [IsAuthenticated, IsMasterOrBilling, ],
        'partial_update': [IsAuthenticated, IsMasterOrBilling, ],
    }

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(company=user.get_company(), is_platforms=False)


class CompanyEditViewSet(PermissionClassByActionMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (IsAuthenticated, )
    permission_classes_by_action = {
        'get_reviews': (IsAuthenticated, IsClientCompany, ),
        'get_partners': (IsAuthenticated, IsClientCompany, ),
    }

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(users=user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'get_review':
            return CompanyReviewSerializer
        if self.action == 'get_partners':
            return ShipperSerializer
        return self.serializer_class

    @action(methods=['get'], detail=True, url_path='reviews')
    def get_reviews(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='partners')
    def get_partners(self, request, *args, **kwargs):
        company = request.user.get_company()
        queryset = Shipper.objects.filter(
            company=company,
            is_partner=True,
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SignUpRequestViewSet(mixins.CreateModelMixin,
                           viewsets.GenericViewSet):
    queryset = SignUpRequest.objects.all()
    serializer_class = SignUpRequestSerializer
    permission_classes = (AllowAny, )


class SignUpCheckView(mixins.RetrieveModelMixin,
                      CheckTokenMixin,
                      generics.GenericAPIView):
    serializer_class = UserBaseSerializer
    permission_classes = (AllowAny, )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object().user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get(self, request):
        return self.retrieve(request)


class UserViewSet(PermissionClassByActionMixin,
                  CreateMixin,
                  viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = (IsAuthenticated, )
    permission_classes_by_action = {
        'create': (IsAuthenticated, IsMaster,),
        'destroy': (IsAuthenticated, IsMaster,),
        'list': (IsAuthenticated, IsMaster,),
        'get_users_list_to_assign': (IsAuthenticated, IsAgentCompany, IsMaster,),
    }

    def get_queryset(self):
        user = self.request.user
        company = user.get_company()
        if self.request.user.get_roles().filter(name='master').exists():
            return self.queryset.filter(companies=company)
        return self.queryset.filter(id=user.id)

    def get_serializer_class(self):
        if self.request.user.get_roles().filter(name='master').exists():
            if self.request.method == 'POST':
                return UserCreateSerializer
            elif self.request.method == 'GET':
                return UserSerializer
            return UserMasterSerializer
        return UserSerializer

    @action(methods=['get'], detail=False, url_path='assign-users-list')
    def get_users_list_to_assign(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(role__groups__name='agent')
        serializer = UserBaseSerializerWithPhoto(queryset, many=True)
        return Response(serializer.data)


class UserSignUpView(CheckTokenMixin,
                     generics.GenericAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSignUpSerializer
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        token = self.get_object()
        new_user = token.user
        serializer = self.get_serializer(new_user, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = authenticate(email=serializer.data['email'], password=serializer.data['confirm_password'])
        if user:
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            data = {
                'token': jwt_encode_handler(payload),
                'user': str(user),
            }
            token.delete()
            return Response(data=data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(mixins.RetrieveModelMixin,
                      generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        return self.request.user

    def get(self, request):
        return self.retrieve(request)


class SelectChoiceView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SelectChoiceSerializer

    def get(self, request, *args, **kwargs):
        data = {}
        models = request.query_params.get('models')
        if models:
            models = models.split(',')
            allowed_models = {
                'frozen_choices': {
                    'choice_type': 'choice',
                    'data': CargoGroup.FROZEN_CHOICES,
                },
                'release_type': {
                    'choice_type': 'model',
                    'data': ReleaseType,
                },
                'packaging_type': {
                    'choice_type': 'model',
                    'data': PackagingType,
                },
                'container_type_sea': {
                    'choice_type': 'model',
                    'data': ContainerType,
                },
                'container_type_air': {
                    'choice_type': 'model',
                    'data': ContainerType,
                },
                'cancellation_reason': {
                    'choice_type': 'choice',
                    'data': CancellationReason.REASON_CHOICES,
                },
            }
            for model in models:
                if model in allowed_models:
                    value = allowed_models.get(model)
                    if (choice_type := value.get('choice_type')) == 'choice':
                        data[model] = choice_to_value_name(value.get('data'))
                    elif choice_type == 'model':
                        queryset = value.get('data').objects.all()
                        if model == 'container_type_sea':
                            queryset = queryset.filter(shipping_mode__shipping_type__title='sea')
                        elif model == 'container_type_air':
                            queryset = queryset.filter(shipping_mode__shipping_type__title='air')
                        data[model] = queryset
            serializer = self.get_serializer(data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
