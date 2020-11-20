from rest_framework import generics, mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from django.contrib.auth import get_user_model, authenticate

from app.core.mixins import PermissionClassByActionMixin, CheckTokenMixin, CreateMixin
from app.core.models import BankAccount, Company, SignUpRequest
from app.core.permissions import IsMaster, IsMasterOrBilling, IsAgentCompanyMaster
from app.core.serializers import CompanySerializer, SignUpRequestSerializer, UserBaseSerializer, UserCreateSerializer, \
    UserSignUpSerializer, BankAccountSerializer, UserMasterSerializer, UserSerializer, SelectChoiceSerializer
from app.core.utils import choice_to_value_name
from app.booking.models import CargoGroup
from app.handling.models import ReleaseType


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
        return self.queryset.filter(company=user.get_company())


class CompanyEditViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (IsAuthenticated, )


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
        'get_users_list_to_assign': (IsAuthenticated, IsAgentCompanyMaster,),
    }

    def get_serializer_class(self):
        if self.request.user.get_roles().filter(name='master').exists():
            if self.request.method == 'POST':
                return UserCreateSerializer
            elif self.request.method == 'GET':
                return UserSerializer
            return UserMasterSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        company = user.get_company()
        if self.request.user.get_roles().filter(name='master').exists():
            return self.queryset.filter(companies=company)
        return self.queryset.filter(id=user.id)

    @action(methods=['get'], detail=False, url_path='assign-users-list')
    def get_users_list_to_assign(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(role__groups__name='agent')
        serializer = UserBaseSerializer(queryset, many=True)
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
            }
            for model in models:
                if model in allowed_models:
                    value = allowed_models.get(model)
                    if (choice_type := value.get('choice_type')) == 'choice':
                        data[model] = choice_to_value_name(value.get('data'))
                    elif choice_type == 'model':
                        data[model] = value.get('data').objects.all()
            serializer = self.get_serializer(data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
