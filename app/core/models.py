from django.db.models import Q
from phonenumber_field.modelfields import PhoneNumberField

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


tax_id_validator = RegexValidator(
    regex=r'^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$',
    message='Invalid format. Must be: 00.000.000/0000-00'
)

branch_validator = RegexValidator(
    regex=r'^\d{4}-\d{1}$',
    message='Invalid format. Must be: 0000-0',
)

bank_account_number_validator = RegexValidator(
    regex=r'^\d+$',
    message='Invalid format. Must contains only numbers',
)

zip_code_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9]+[-]?[a-zA-Z0-9]+$',
    message='Invalid format. Must contains only letters, numbers or one hyphen. '
            'A zip code cannot begin or end with a hyphen.',
)


class CustomUserManager(BaseUserManager):
    """
    Define a model manager for User model with no username field.
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular User with the given email and password.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Base user model.
    """

    username_validator = None
    username = None

    email = models.EmailField(
        _('email address'),
        unique=True,
    )
    phone = PhoneNumberField(
        _('Phone number'),
        max_length=13,
        null=True,
    )
    position = models.CharField(
        _('Position In Company'),
        max_length=100,
    )
    photo = models.ImageField(
        _('Profile Photo'),
        max_length=255,
        blank=True,
        null=True,
        upload_to='profile_pics',
        help_text='User profile photo.'
    )
    companies = models.ManyToManyField(
        'Company',
        related_name='users',
        through='Role',
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def get_roles(self):
        return self.role_set.first().groups.all()

    def set_roles(self, roles_list):
        query_roles_list = [Q(name=role) for role in roles_list]
        groups = Group.objects.filter(Q(*query_roles_list, _connector='OR'))
        self.role_set.first().groups.set(groups)

    @property
    def roles(self):
        return self.get_roles().values_list('name', flat=True)


class Company(models.Model):
    """
    Model for company registration.
    """

    FREIGHT_FORWARDER = 'agent'
    CLIENT = 'client'

    COMPANY_TYPE_CHOICES = (
        (FREIGHT_FORWARDER, 'Freight forwarder'),
        (CLIENT, 'Client'),
    )

    type = models.CharField(
        _('Company Type'),
        max_length=100,
        choices=COMPANY_TYPE_CHOICES,
    )
    name = models.CharField(
        _('Company Name'),
        max_length=100,
    )
    address_line_first = models.CharField(
        _('First address line'),
        max_length=100,
        null=True,
    )
    address_line_second = models.CharField(
        _('Second address line'),
        max_length=100,
        blank=True,
        null=True,
    )
    state = models.CharField(
        _('State'),
        max_length=100,
    )
    city = models.CharField(
        _('City'),
        max_length=100,
    )
    zip_code = models.CharField(
        _('Zip Code'),
        max_length=12,
        validators=[zip_code_validator],
    )
    phone = PhoneNumberField(
        _('Phone number'),
        max_length=13,
        unique=True,
    )
    tax_id = models.CharField(
        _('Tax id Number'),
        max_length=18,
        validators=[tax_id_validator],
        unique=True,
    )
    employees_number = models.PositiveIntegerField(
        _('Number of employees in company'),
        default=1,
    )
    website = models.CharField(
        _('Company website'),
        max_length=100,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.name}'


class SignUpRequest(models.Model):
    """
    Model for sing up request info.
    """

    type = models.CharField(
        _('Company Type'),
        max_length=100,
        choices=Company.COMPANY_TYPE_CHOICES,
    )
    name = models.CharField(
        _('Company Name'),
        max_length=100,
    )
    address_line_first = models.CharField(
        _('First address line'),
        max_length=100,
        null=True,
    )
    address_line_second = models.CharField(
        _('Second address line'),
        max_length=100,
        blank=True,
        null=True,
    )
    state = models.CharField(
        _('State'),
        max_length=100,
    )
    city = models.CharField(
        _('City'),
        max_length=100,
    )
    zip_code = models.CharField(
        _('Zip Code'),
        max_length=12,
        validators=[zip_code_validator],
    )
    phone = PhoneNumberField(
        _('Phone number'),
        max_length=13,
        unique=True,
    )
    tax_id = models.CharField(
        _('Tax id Number (00.000.000/0000-00)'),
        max_length=18,
        validators=[tax_id_validator],
    )
    employees_number = models.PositiveIntegerField(
        _('Number of employees in company'),
        default=1,
    )
    website = models.CharField(
        _('Company website'),
        max_length=100,
        blank=True,
        null=True,
    )
    approved = models.BooleanField(
        _('Approved'),
        default=False,
    )
    email = models.EmailField(
        _('Email address'),
        unique=True,
    )
    first_name = models.CharField(
        _('First name'),
        max_length=150,
        null=True,
    )
    last_name = models.CharField(
        _('Last name'),
        max_length=150,
        null=True,
    )
    master_phone = PhoneNumberField(
        _('Phone number'),
        max_length=13,
        null=True,
    )
    position = models.CharField(
        _('Position in company'),
        max_length=100,
        null=True,
    )

    def __str__(self):
        return f'Sign up request of company "{self.name}"'


class SignUpToken(models.Model):
    """
    Model for sign up token info.
    """

    token = models.CharField(
        _('Sign Up Token'),
        max_length=30,
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )


class Role(models.Model):
    """
    Model to connect company and users through django groups.
    """

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="users",
    )

    def __str__(self):
        return f'{self.user}, "{self.company}", {list(self.groups.all().values_list("name", flat=True))}'


class BankAccount(models.Model):
    """
    Model for bank account info.
    """

    SAVINGS = 'savings'
    CHECKING = 'checking'

    ACCOUNT_TYPE_CHOICES = (
        (SAVINGS, 'Savings'),
        (CHECKING, 'Checking'),
    )

    bank_name = models.CharField(
        _('Bank Name'),
        max_length=100,
    )
    branch = models.CharField(
        _('Branch Number (0000-0)'),
        max_length=6,
        validators=[branch_validator],
    )
    number = models.CharField(
        _('Account Number'),
        max_length=50,
        validators=[bank_account_number_validator],
        unique=True,
    )
    account_type = models.CharField(
        _('Account Type'),
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='bank_accounts',
    )
    is_default = models.BooleanField(
        _('Is default bank account or not'),
        default=False,
    )

    class Meta:
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')

    def __str__(self):
        return f'{self.__class__.__name__} of company {self.company}'

    def save(self, *args, **kwargs):
        if self.is_default:
            BankAccount.objects.filter(company=self.company).update(is_default=False)
        super(BankAccount, self).save(*args, **kwargs)


class Shipper(models.Model):
    """
    Model for the shipper company.
    """

    name = models.CharField(
        _('Company Name'),
        max_length=100,
    )
    address_line_first = models.CharField(
        _('First address line'),
        max_length=100,
        null=True,
    )
    address_line_second = models.CharField(
        _('Second address line'),
        max_length=100,
        blank=True,
        null=True,
    )
    state = models.CharField(
        _('State'),
        max_length=100,
        null=True,
    )
    city = models.CharField(
        _('City'),
        max_length=100,
    )
    zip_code = models.CharField(
        _('Zip Code'),
        max_length=12,
        validators=[zip_code_validator],
        null=True,
    )
    contact_name = models.CharField(
        _('Shippers contact name'),
        max_length=100,
    )
    phone = PhoneNumberField(
        _('Phone number'),
        max_length=13,
    )
    phone_additional = PhoneNumberField(
        _('Additional phone number'),
        max_length=13,
        null=True,
    )
    email = models.EmailField(
        _('email address'),
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'Shipper {self.name}, {self.phone}'
