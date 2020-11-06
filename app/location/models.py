from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    """
    Country model.
    """

    code = models.CharField(
        _('Country Code'),
        max_length=2,
    )
    name = models.CharField(
        _('Country Name'),
        max_length=100,
    )
    currency = models.ForeignKey(
        'handling.Currency',
        null=True,
        on_delete=models.SET_NULL,
    )
    is_active = models.BooleanField(
        _('Country is active'),
        default=True,
    )
    chosen_for_platform = models.BooleanField(
        _('Country was chosen as main for platform'),
        default=False,
    )

    def __str__(self):
        return f'{self.name} ({self.code})'

    def save(self, *args, **kwargs):
        if self.chosen_for_platform:
            Country.objects.all().update(chosen_for_platform=False)
        super(Country, self).save(*args, **kwargs)


class Region(models.Model):
    """
    Administrative region model.
    """

    name = models.CharField(
        _('State Name'),
        max_length=100,
    )

    def __str__(self):
        return f'Region {self.name}'


class State(models.Model):
    """
    State model.
    """

    code = models.CharField(
        _('State Code'),
        max_length=3,
    )
    name = models.CharField(
        _('State Name'),
        max_length=100,
    )
    country = models.ForeignKey(
        'Country',
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(
        _('State is active'),
        default=True,
    )
    region = models.ForeignKey(
        'Region',
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.name} ({self.code})'


class InternationalZone(models.Model):
    """
    International zone model.
    """

    TAX = 'TAX'
    RAT = 'RAT'
    RPT = 'RPT'
    ZONE_CHOICES = (
        (TAX, 'TAX'),
        (RAT, 'RAT'),
        (RPT, 'RPT'),
    )

    code = models.CharField(
        _('Zone Code'),
        max_length=3,
    )
    name = models.CharField(
        _('Zone Name'),
        max_length=100,
    )
    zone_type = models.CharField(
        _('Zone type'),
        max_length=3,
        choices=ZONE_CHOICES,
    )
    carrier_or_customer = models.CharField(
        _('Carrier or customer'),
        max_length=50,
        null=True,
    )

    def __str__(self):
        return f'Zone {self.name} ({self.code})'
