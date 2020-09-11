from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from django.db import transaction
from django.contrib.auth import get_user_model, password_validation
from django.core import exceptions

from app.core.models import BankAccount, Company, SignUpRequest, Role
from app.core.utils import process_sign_up_token


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'id',
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


class UserCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    position = serializers.CharField(max_length=100)
    roles = serializers.ListField(write_only=True)

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


class UserBaseSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

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

    def get_roles(self, obj):
        return obj.get_roles().values_list('name', flat=True)


class UserSerializer(UserBaseSerializer):
    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + (
            'phone',
            'photo',
        )


class UserMasterSerializer(UserSerializer):
    roles = serializers.ListField(write_only=True)

    def update(self, instance, validated_data):
        roles = validated_data.pop('roles')
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
    password = serializers.CharField(min_length=8, max_length=25)
    confirm_password = serializers.CharField(min_length=8, max_length=25)
    photo = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        errors = {}
        try:
            password_validation.validate_password(attrs.get('password'))
            if attrs.get('password') != attrs.get('confirm_password'):
                errors['password'] = "Password fields didn't match."
                raise serializers.ValidationError(errors)
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)
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


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = (
            'bank_name',
            'branch',
            'number',
            'account_type',
        )

    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.companies.first()
        bank_account = super().create(validated_data)
        return bank_account
