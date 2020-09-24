from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from django.db import transaction
from django.contrib.auth import get_user_model

from app.core.models import BankAccount, Company, SignUpRequest, Role
from app.core.utils import process_sign_up_token
from app.core.validators import PasswordValidator


class CompanyBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'id',
        )


class CompanySerializer(CompanyBaseSerializer):
    class Meta(CompanyBaseSerializer.Meta):
        fields = CompanyBaseSerializer.Meta.fields + (
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
        )


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
            'master_email',
        )

    def validate(self, attrs):
        errors = {}
        phone = attrs.get('phone')
        email = attrs.get('master_email')
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
        company = self.context['request'].user.companies.first()
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
        if attrs.get('password') != attrs.get('confirm_password'):
            errors['password'] = "Password fields didn't match."
            raise serializers.ValidationError(errors)
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.set_password(password)
        instance.save()
        return instance


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = (
            'id',
            'bank_name',
            'branch',
            'number',
            'account_type',
            'company',
            'is_default',
        )

    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.companies.first()
        bank_account = super().create(validated_data)
        return bank_account
