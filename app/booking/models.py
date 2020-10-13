from django.contrib.auth import get_user_model
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
    )
    is_active = models.BooleanField(
        _('Freight rate is active or paused'),
        default=True,
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
