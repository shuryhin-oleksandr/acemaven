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
    is_main = models.BooleanField(
        _('Country was chosen as main for platform'),
        default=False,
    )

    def __str__(self):
        return f'{self.name} ({self.code})'

    def save(self, *args, **kwargs):
        if self.is_main:
            Country.objects.all().update(is_main=False)
        super(Country, self).save(*args, **kwargs)
