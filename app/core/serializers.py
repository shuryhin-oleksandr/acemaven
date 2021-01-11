from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.booking.models import Booking
from app.core.models import BankAccount, Company, SignUpRequest, Role, Shipper, Review
from app.core.utils import process_sign_up_token, get_average_company_rating
from app.core.validators import PasswordValidator
from app.handling.models import GeneralSetting
from app.handling.serializers import ReleaseTypeSerializer, PackagingTypeBaseSerializer, ContainerTypesBaseSerializer


class ReviewBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = (
            'id',
            'rating',
            'comment',
            'operation',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['reviewer'] = user
        review = super().create(validated_data)
        return review


class ReviewListSerializer(ReviewBaseSerializer):
    route = serializers.SerializerMethodField()
    company = serializers.CharField(source='reviewer.get_company')
    reviewer_photo = serializers.ImageField(source='reviewer.photo')

    class Meta(ReviewBaseSerializer.Meta):
        model = Review
        fields = ReviewBaseSerializer.Meta.fields + (
            'date_created',
            'route',
            'company',
            'reviewer_photo',
        )

    def get_route(self, obj):
        freight_rate = obj.operation.freight_rate
        return f'{freight_rate.shipping_mode.title}, {freight_rate.origin.code}-{freight_rate.destination.code}'


class CompanyBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'id',
            'type',
        )


class CompanySerializer(CompanyBaseSerializer):
    class Meta(CompanyBaseSerializer.Meta):
        fields = CompanyBaseSerializer.Meta.fields + (
            'name',
            'address_line_first',
            'address_line_second',
            'state',
            'city',
            'zip_code',
            'phone',
            'tax_id',
            'employees_number',
            'website',
        )


class CompanyReviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    shipping_types = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    operations_are_done = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    reviews = ReviewListSerializer(source='get_reviews', many=True)

    class Meta:
        model = Company
        fields = (
            'id',
            'name',
            'shipping_types',
            'date_created',
            'operations_are_done',
            'rating',
            'reviews',
        )

    def get_name(self, obj):
        general_settings = GeneralSetting.load()
        show_freight_forwarder_name = general_settings.show_freight_forwarder_name
        return obj.name if show_freight_forwarder_name == GeneralSetting.ALL else '*Agent company name'

    def get_shipping_types(self, obj):
        return obj.freight_rates.\
            distinct('shipping_mode__shipping_type').\
            values_list('shipping_mode__shipping_type__title', flat=True)

    def get_date_created(self, obj):
        return f'{obj.date_created.strftime("%m %B %Y")} ' \
               f'({(timezone.localtime().date() - obj.date_created).days // 365} YEARS)'

    def get_operations_are_done(self, obj):
        return Booking.objects.filter(
            freight_rate__company=obj,
            status=Booking.COMPLETED,
        ).count()

    def get_rating(self, obj):
        return get_average_company_rating(obj)


class SignUpRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignUpRequest
        fields = (
            'type',
            'name',
            'address_line_first',
            'address_line_second',
            'state',
            'city',
            'zip_code',
            'phone',
            'tax_id',
            'employees_number',
            'website',
            'email',
            'first_name',
            'last_name',
            'master_phone',
            'position',
        )

    def validate(self, attrs):
        errors = {}
        phone = attrs.get('phone')
        email = attrs.get('email')
        tax_id = attrs.get('tax_id')
        users = get_user_model().objects.filter(email=email).exists()
        companies = Company.objects.filter(phone=phone).exists()
        tax_ids = Company.objects.filter(tax_id=tax_id).exists()
        if users:
            errors['master_email'] = 'User with provided email already exists.'
        if companies:
            errors['phone'] = 'Company with provided phone number already exists.'
        if tax_ids:
            errors['tax_id'] = 'Company with provided tax id already exists.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class UserCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    position = serializers.CharField(required=False)
    roles = serializers.ListField()

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'position',
            'roles',
        )

    def validate(self, attrs):
        users = get_user_model().objects.filter(email=attrs.get('email'))
        if users.exists():
            errors = dict()
            errors['email'] = f'Email [{attrs.get("email")}] already exists.'
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        roles = validated_data.pop('roles')
        user = get_user_model().objects.create(**validated_data)
        company = self.context['request'].user.get_company()
        Role.objects.create(user=user, company=company)
        user.set_roles(roles)
        process_sign_up_token(user)
        return user

    def get_get_role(self, obj):
        return obj.get_roles().values_list('name', flat=True)


class UserBaseSerializer(serializers.ModelSerializer):
    roles = serializers.ListField(read_only=True)
    companies = CompanyBaseSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'position',
            'companies',
            'roles',
        )


class UserBaseSerializerWithPhoto(UserBaseSerializer):
    class Meta(UserBaseSerializer.Meta):
        model = get_user_model()
        fields = UserBaseSerializer.Meta.fields + (
            'photo',
        )


class UserSerializer(UserBaseSerializer):
    password = serializers.CharField(min_length=8, max_length=25, write_only=True, validators=(PasswordValidator(), ))

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + (
            'phone',
            'photo',
            'password',
        )

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
            instance.save()
        super().update(instance, validated_data)
        return instance


class UserMasterSerializer(UserSerializer):
    roles = serializers.ListField()

    def update(self, instance, validated_data):
        roles = validated_data.pop('roles', None)
        if roles:
            instance.set_roles(roles)
        super().update(instance, validated_data)
        return instance


class UserSignUpSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = PhoneNumberField()
    position = serializers.CharField(max_length=100)
    password = serializers.CharField(min_length=8, max_length=25, validators=(PasswordValidator(), ))
    confirm_password = serializers.CharField(min_length=8, max_length=25)
    photo = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        errors = {}
        users = get_user_model().objects.exclude(id=self.instance.id).filter(email=attrs.get('email'))
        if users.exists():
            errors['email'] = f'Email [{attrs.get("email")}] already exists.'
        if attrs.get('password') != attrs.get('confirm_password'):
            errors['password'] = "Password fields didn't match."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.set_password(password)
        instance.save()
        return instance


class BankAccountBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = (
            'id',
            'bank_name',
            'bank_number',
            'branch',
            'number',
        )


class BankAccountSerializer(BankAccountBaseSerializer):
    company = serializers.IntegerField(source='company.id', read_only=True)

    class Meta(BankAccountBaseSerializer.Meta):
        model = BankAccount
        fields = BankAccountBaseSerializer.Meta.fields + (
            'account_type',
            'company',
            'is_default',
        )

    def create(self, validated_data):
        company = self.context['request'].user.get_company()
        validated_data['company'] = company
        if not company.bank_accounts.exists():
            validated_data['is_default'] = True
        bank_account = super().create(validated_data)
        return bank_account


class SelectChoiceSerializer(serializers.Serializer):
    frozen_choices = serializers.ListField(required=False)
    release_type = ReleaseTypeSerializer(many=True, required=False)
    packaging_type = PackagingTypeBaseSerializer(many=True, required=False)
    container_type_sea = ContainerTypesBaseSerializer(many=True, required=False)
    container_type_air = ContainerTypesBaseSerializer(many=True, required=False)
    cancellation_reason = serializers.ListField(required=False)


class ShipperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipper
        fields = (
            'id',
            'name',
            'address_line_first',
            'address_line_second',
            'state',
            'city',
            'zip_code',
            'contact_name',
            'phone',
            'phone_additional',
            'email',
        )
