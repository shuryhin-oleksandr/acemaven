from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Surcharge(models.Model):
    """
    Surcharges model.
    """

    IMPORT = 'import'
    EXPORT = 'export'
    DIRECTION_CHOICES = (
        (IMPORT, 'Import'),
        (EXPORT, 'Export'),
    )

    carrier = models.ForeignKey(
        'handling.Carrier',
        on_delete=models.CASCADE,
        related_name='surcharges',
    )
    direction = models.CharField(
        _('Surcharge direction, whether import or export'),
        max_length=6,
        choices=DIRECTION_CHOICES,
    )
    location = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
    )
    start_date = models.DateField(
        _('Surcharge start date'),
    )
    expiration_date = models.DateField(
        _('Surcharge expiration date'),
    )
    temporary = models.BooleanField(
        _('Temporary surcharge or not'),
        default=False,
    )
    shipping_mode = models.ForeignKey(
        'handling.ShippingMode',
        on_delete=models.CASCADE,
        related_name='surcharges',
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='surcharges',
    )
    container_types = models.ManyToManyField(
        'handling.ContainerType',
        related_name='surcharges',
        through='UsageFee',
    )
    additional_surcharges = models.ManyToManyField(
        'AdditionalSurcharge',
        related_name='surcharges',
        through='Charge',
    )

    def __str__(self):
        return f'Surcharge for {self.direction}, {self.location}, {self.expiration_date}'


class UsageFee(models.Model):
    """
    Usage Fee / Handling surcharges model.
    Through model for surcharges and container types.
    """

    container_type = models.ForeignKey(
        'handling.ContainerType',
        on_delete=models.CASCADE,
    )
    surcharge = models.ForeignKey(
        'Surcharge',
        on_delete=models.CASCADE,
        related_name='usage_fees',
    )
    currency = models.ForeignKey(
        'handling.Currency',
        on_delete=models.CASCADE,
    )
    charge = models.DecimalField(
        _('Charge amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )
    date_updated = models.DateTimeField(
        _('Date and time usage fee was updated'),
        auto_now=True,
    )

    def __str__(self):
        return f'{self.container_type}, {self.currency}, {self.charge}'


class Charge(models.Model):
    """
    Through model for surcharges and additional surcharges.
    """

    WM = 'w/m'
    PER_WEIGHT = 'per_weight'
    PER_NO_OF_PACKS = 'per_no_of_packs'
    FIXED = 'fixed'
    CONDITIONS_CHOICES = (
        (WM, 'w/m'),
        (PER_WEIGHT, 'per weight'),
        (PER_NO_OF_PACKS, 'per no. of packs'),
        (FIXED, 'fixed'),
    )

    additional_surcharge = models.ForeignKey(
        'AdditionalSurcharge',
        on_delete=models.CASCADE,
    )
    surcharge = models.ForeignKey(
        'Surcharge',
        on_delete=models.CASCADE,
        related_name='charges',
    )
    currency = models.ForeignKey(
        'handling.Currency',
        on_delete=models.CASCADE,
    )
    charge = models.DecimalField(
        _('Charge amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    conditions = models.CharField(
        _('Conditions'),
        max_length=20,
        choices=CONDITIONS_CHOICES,
        default=FIXED,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )
    date_updated = models.DateTimeField(
        _('Date and time usage fee was updated'),
        auto_now=True,
    )

    def __str__(self):
        return f'{self.currency}, {self.charge}, {self.conditions}'


class AdditionalSurcharge(models.Model):
    """
    Additional surcharges model.
    """

    title = models.CharField(
        _('Additional surcharge title'),
        max_length=100,
    )
    shipping_mode = models.ManyToManyField(
        'handling.ShippingMode',
        related_name='additional_surcharges',
    )
    is_dangerous = models.BooleanField(
        _('Is dangerous'),
        default=False,
    )
    is_cold = models.BooleanField(
        _('Is cold'),
        default=False,
    )
    is_handling = models.BooleanField(
        _('Is handling'),
        default=False,
    )
    is_document = models.BooleanField(
        _('Is document'),
        default=False,
    )
    is_other = models.BooleanField(
        _('Is other'),
        default=False,
    )

    def __str__(self):
        return f'{self.title}'


class FreightRate(models.Model):
    """
    Freight rate model.
    """

    carrier = models.ForeignKey(
        'handling.Carrier',
        on_delete=models.CASCADE,
        related_name='freight_rates',
    )
    carrier_disclosure = models.BooleanField(
        _('Whether carrier name disclosed or not'),
        default=False,
    )
    origin = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        related_name='origin_freight_rates',
    )
    destination = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        related_name='destination_freight_rates',
    )
    transit_time = models.PositiveIntegerField(
        _('Transit time in days'),
        null=True,
    )
    is_active = models.BooleanField(
        _('Freight rate is active or paused'),
        default=True,
    )
    temporary = models.BooleanField(
        _('Temporary freight rate or not'),
        default=False,
    )
    shipping_mode = models.ForeignKey(
        'handling.ShippingMode',
        on_delete=models.CASCADE,
        related_name='freight_rates',
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='freight_rates',
    )


class Rate(models.Model):
    """
    Model for concrete amount of freight rate.
    """

    currency = models.ForeignKey(
        'handling.Currency',
        on_delete=models.CASCADE,
    )
    rate = models.DecimalField(
        _('Rate amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    start_date = models.DateField(
        _('Rate start date'),
        null=True,
    )
    expiration_date = models.DateField(
        _('Rate expiration date'),
        null=True,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )
    date_updated = models.DateTimeField(
        _('Date and time rate was updated'),
        auto_now=True,
    )
    freight_rate = models.ForeignKey(
        'FreightRate',
        on_delete=models.CASCADE,
        related_name='rates',
    )
    container_type = models.ForeignKey(
        'handling.ContainerType',
        on_delete=models.CASCADE,
        null=True,
    )
    surcharges = models.ManyToManyField(
        'Surcharge',
        related_name='rates',
    )


class Booking(models.Model):
    """
    Model for booking instance.
    """

    date_from = models.DateField(
        _('Booing date from'),
    )
    date_to = models.DateField(
        _('Booking date to'),
    )
    is_paid = models.BooleanField(
        _('Whether booking paid or not'),
        default=False,
    )
    confirmed = models.BooleanField(
        _('Booking confirmed or not'),
        default=False,
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
    )
    release_type = models.ForeignKey(
        'handling.ReleaseType',
        on_delete=models.SET_NULL,
        null=True,
    )
    number_of_documents = models.PositiveIntegerField(
        _('Number of documents for chosen release type'),
        validators=[MinValueValidator(1)],
        null=True,
    )
    freight_rate = models.ForeignKey(
        'FreightRate',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    shipper = models.ForeignKey(
        'core.Shipper',
        on_delete=models.SET_NULL,
        related_name='bookings',
        null=True,
    )

    def __str__(self):
        return f'Booking of rate [{self.freight_rate}]'


class CargoGroup(models.Model):
    """
    Model for cargo group.
    """

    FROZEN = 'frozen'
    COLD = 'cold'
    FROZEN_CHOICES = (
        (FROZEN, 'Frozen'),
        (COLD, 'Chilled'),
    )

    KG = 'kg'
    T = 't'
    WEIGHT_MEASUREMENT_CHOICES = (
        (KG, 'kg'),
        (T, 't'),
    )

    CM = 'cm'
    M = 'm'
    LENGTH_MEASUREMENT_CHOICES = (
        (CM, 'cm'),
        (M, 'm'),
    )

    container_type = models.ForeignKey(
        'handling.ContainerType',
        on_delete=models.CASCADE,
        null=True,
    )
    packaging_type = models.ForeignKey(
        'handling.PackagingType',
        on_delete=models.CASCADE,
        null=True,
    )
    weight_measurement = models.CharField(
        _('Weight Measurement'),
        max_length=2,
        choices=WEIGHT_MEASUREMENT_CHOICES,
        null=True,
    )
    length_measurement = models.CharField(
        _('Length Measurement'),
        max_length=2,
        choices=LENGTH_MEASUREMENT_CHOICES,
        null=True,
    )
    volume = models.PositiveIntegerField(
        _('Number of items'),
        validators=[MinValueValidator(1)],
        null=True,
    )
    height = models.DecimalField(
        _('Height'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    length = models.DecimalField(
        _('Length'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    width = models.DecimalField(
        _('Width'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    weight = models.DecimalField(
        _('Weight'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    total_wm = models.DecimalField(
        _('Total w/m'),
        max_digits=15,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    dangerous = models.BooleanField(
        _('Dangerous freight'),
        default=False,
    )
    frozen = models.CharField(
        _('Frozen or chilled cargo'),
        max_length=10,
        choices=FROZEN_CHOICES,
        null=True,
    )
    description = models.CharField(
        _('Cargo description'),
        max_length=100,
        null=True,
    )
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='cargo_groups',
        null=True,
    )
    quote = models.ForeignKey(
        'Quote',
        on_delete=models.CASCADE,
        related_name='quote_cargo_groups',
        null=True,
    )

    def __str__(self):
        return f'Cargo group [{self.id}] of booking [{self.booking}]'


class Quote(models.Model):
    """
    Model for quote.
    """

    origin = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        related_name='origin_quotes',
    )
    destination = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        related_name='destination_quotes',
    )
    shipping_mode = models.ForeignKey(
        'handling.ShippingMode',
        on_delete=models.CASCADE,
        related_name='quotes',
    )
    date_from = models.DateField(
        _('Quote start date'),
    )
    date_to = models.DateField(
        _('Quote expiration date'),
    )
    date_created = models.DateField(
        _('Quote creation date'),
        auto_now_add=True,
    )
    is_active = models.BooleanField(
        _('Quote is active or paused'),
        default=True,
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='quotes',
    )
    freight_rates = models.ManyToManyField(
        'FreightRate',
        related_name='quotes',
        through='Status',
    )

    def __str__(self):
        return f'Quote {self.origin.code} - {self.destination.code}'


class Status(models.Model):
    """
    Through model for quotes and freight rates.
    """

    REJECTED = 'rejected'
    SUBMITTED = 'submitted'
    STATUS_CHOICES = (
        (REJECTED, 'Rejected'),
        (SUBMITTED, 'Submitted'),
    )

    quote = models.ForeignKey(
        'Quote',
        on_delete=models.CASCADE,
        related_name='statuses',
    )
    freight_rate = models.ForeignKey(
        'FreightRate',
        on_delete=models.CASCADE,
        related_name='statuses',
        null=True
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='statuses',
        null=True,
    )
    status = models.CharField(
        _('Quote - freight rate status'),
        max_length=9,
        choices=STATUS_CHOICES,
    )
    is_viewed = models.BooleanField(
        _('Offer is viewed'),
        default=False,
    )
