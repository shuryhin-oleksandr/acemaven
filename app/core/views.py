from rest_framework import generics, mixins, viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from django.contrib.auth import get_user_model, authenticate

from app.core.models import BankAccount, Company, SignUpRequest, SignUpToken
from app.core.permissions import IsMaster, IsMasterOrBilling
from app.core.serializers import CompanySerializer, SignUpRequestSerializer, UserBaseSerializer, UserCreateSerializer, \
    UserSignUpSerializer, BankAccountSerializer, UserMasterSerializer, UserSerializer, SelectChoiceSerializer
from app.core.utils import choice_to_value_name
from app.booking.models import CargoGroup


class CheckTokenMixin:
    """
    Class, that provides custom get_object() method.
    """

    def get_object(self):
        token = self.request.query_params.get('token')
        obj = get_object_or_404(SignUpToken.objects.all(), token=token)
        return obj


class CreateMixin:
    """
    Class, that provides custom create() method for bulk object creation optionally.
    """

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BankAccountViewSet(CreateMixin, viewsets.ModelViewSet):
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
        return self.queryset.filter(company=user.companies.first())


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


class UserViewSet(CreateMixin,
                  viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = (IsAuthenticated, )
    permission_classes_by_action = {
        'create': [IsAuthenticated, IsMaster, ],
        'destroy': [IsAuthenticated, IsMaster, ],
        'list': [IsAuthenticated, IsMaster, ],
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
        company = user.companies.first()
        if self.request.user.get_roles().filter(name='master').exists():
            return self.queryset.filter(companies=company)
        return self.queryset.filter(id=user.id)


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
                'frozen_choices': CargoGroup.FROZEN_CHOICES,
            }
            for model in models:
                if model in allowed_models:
                    data[model] = choice_to_value_name(allowed_models[model])
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
