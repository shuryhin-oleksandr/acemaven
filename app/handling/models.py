from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _


class ShippingType(models.Model):
    """
    Shipping type model.
    """

    title = models.CharField(
        _('Shipping Type Title'),
        max_length=20,
    )


class ShippingMode(models.Model):
    """
    Shipping mode model.
    """

    title = models.CharField(
        _('Shipping Mode Title'),
        max_length=100,
    )
    shipping_type = models.ForeignKey(
        'ShippingType',
        on_delete=models.CASCADE,
        related_name='shipping_modes',
    )


class PackagingType(models.Model):
    """
    Packaging type model.
    """

    code = models.CharField(
        _('Packaging code'),
        max_length=3,
    )
    description = models.CharField(
        _('Description'),
        max_length=100,
    )
    description_pt = models.CharField(
        _('Description PT'),
        max_length=100,
    )
    height = models.DecimalField(
        _('Height'),
        max_digits=15,
        decimal_places=2,
    )
    length = models.DecimalField(
        _('Length'),
        max_digits=15,
        decimal_places=2,
    )
    width = models.DecimalField(
        _('Width'),
        max_digits=15,
        decimal_places=2,
    )
    dimension_unit = models.CharField(
        _('Dimension unit'),
        max_length=10,
    )
    weight = models.DecimalField(
        _('Weight'),
        max_digits=15,
        decimal_places=2,
    )
    weight_unit = models.CharField(
        _('Weight unit'),
        max_length=10,
    )


class ContainerType(models.Model):
    """
    Container type model.
    """

    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )
    code = models.CharField(
        _('Container code'),
        max_length=50,
    )
    description_pt = models.CharField(
        _('Description PT'),
        max_length=100,
    )
    description = models.CharField(
        _('Description'),
        max_length=100,
    )
    mode = models.CharField(
        _('Mode'),
        max_length=20,
        null=True,
    )
    fcl_type = models.CharField(
        _('FCL type'),
        max_length=10,
    )
    iata_class = models.DecimalField(
        _('IATA class'),
        max_digits=15,
        decimal_places=2,
        null=True,
    )
    teu = models.DecimalField(
        _('TEU'),
        max_digits=15,
        decimal_places=2,
    )
    height = models.DecimalField(
        _('Height'),
        max_digits=15,
        decimal_places=2,
    )
    length = models.DecimalField(
        _('Length'),
        max_digits=15,
        decimal_places=2,
    )
    width = models.DecimalField(
        _('Width'),
        max_digits=15,
        decimal_places=2,
    )
    gross_weight = models.DecimalField(
        _('Gross weight'),
        max_digits=15,
        decimal_places=2,
    )
    tare_weight = models.DecimalField(
        _('Tare weight'),
        max_digits=15,
        decimal_places=2,
    )
    capacity = models.DecimalField(
        _('Capacity (M3)'),
        max_digits=15,
        decimal_places=2,
        null=True,
    )
    iso = models.CharField(
        _('ISO'),
        max_length=10,
        null=True,
    )
    iso_type = models.CharField(
        _('ISO type'),
        max_length=10,
        null=True,
    )
    iso_size = models.CharField(
        _('ISO size'),
        max_length=100,
        null=True,
    )
    iso_description = models.CharField(
        _('ISO description'),
        max_length=150,
        null=True,
    )


class IMOClass(models.Model):
    """
    IMO class model.
    """

    title = models.CharField(
        _('IMO class title'),
        max_length=150,
    )
    imo_class = models.CharField(
        _('IMO class'),
        max_length=50,
    )


class ReleaseType(models.Model):
    """
    Release type model.
    """

    title = models.CharField(
        _('Release type title'),
        max_length=150,
    )
    code = models.CharField(
        _('Release code'),
        max_length=3,
    )


class Carrier(models.Model):
    """
    Carrier model.
    """

    title = models.CharField(
        _('Carrier title'),
        max_length=100,
    )
    shipping_type = models.ForeignKey(
        'ShippingType',
        on_delete=models.CASCADE,
        related_name='carriers',
    )


class Airline(models.Model):
    """
    Airline model.
    """

    two_char_code = models.CharField(
        _('Two char airline code'),
        max_length=2,
        null=True,
    )
    three_char_code = models.CharField(
        _('Three char airline code'),
        max_length=3,
        null=True,
    )
    numeric_code = models.CharField(
        _('Numeric airline code'),
        max_length=3,
        null=True,
    )
    name = models.CharField(
        _('Airline title'),
        max_length=100,
    )
    name_additional = models.CharField(
        _('Airline additional title'),
        max_length=100,
        null=True,
    )
    address = models.CharField(
        _('First address line'),
        max_length=100,
        null=True,
    )
    address_additional = models.CharField(
        _('Additional address line'),
        max_length=100,
        null=True,
    )
    city = models.CharField(
        _('Airline city'),
        max_length=50,
        null=True,
    )
    state = models.ForeignKey(
        'location.State',
        null=True,
        on_delete=models.CASCADE,
    )
    postcode = models.CharField(
        _('Airline postcode'),
        max_length=20,
        null=True,
    )
    cass_controlled = models.BooleanField(
        _('CASS controled'),
        default=False,
    )

    def __str__(self):
        return f'{self.name} ({self.three_char_code})'


class CommonFee(models.Model):
    """
    Base abstract fee class for local and global fee models.
    """

    BOOKING = 'booking'
    SERVICE = 'service'
    FEE_TYPE_CHOICES = (
        (BOOKING, 'Booking Fee'),
        (SERVICE, 'Service Fee'),
    )

    FIXED = 'fixed'
    PERCENT = 'percent'
    VALUE_TYPE_CHOICES = (
        (FIXED, 'Fixed value'),
        (PERCENT, 'Percentage')
    )

    title = models.CharField(
        _('Fee title'),
        max_length=50,
    )
    fee_type = models.CharField(
        _('Fee type'),
        max_length=10,
        choices=FEE_TYPE_CHOICES,
    )
    is_active = models.BooleanField(
        _('Fee enabled'),
        default=True,
    )
    value = models.DecimalField(
        _('Fee value'),
        max_digits=15,
        decimal_places=2,
    )
    value_type = models.CharField(
        _('Value type'),
        max_length=10,
        choices=VALUE_TYPE_CHOICES,
    )

    class Meta:
        abstract = True


class GlobalFee(CommonFee):
    """
    Global fee model.
    """

    shipping_mode = models.ForeignKey(
        'ShippingMode',
        on_delete=models.CASCADE,
        related_name='global_fees',
    )


class LocalFee(CommonFee):
    """
    Local fee model.
    """

    shipping_mode = models.ForeignKey(
        'ShippingMode',
        on_delete=models.CASCADE,
        related_name='local_fees',
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='fees',
    )


class Currency(models.Model):
    """
    Currency model.
    """

    code = models.CharField(
        _('Currency three char code'),
        max_length=3,
    )

    def __str__(self):
        return f'{self.code}'


class Port(gis_models.Model):
    """
    Ports and Airports model.
    """

    code = models.CharField(
        _('Port Code'),
        max_length=5,
    )
    name = models.CharField(
        _('Port Name'),
        max_length=100,
    )
    iata = models.CharField(
        _('IATA'),
        max_length=3,
        null=True,
    )
    coordinates = gis_models.PointField(
        _('Port coordinates'),
        null=True,
    )
    timezone = models.CharField(
        _('Port timezone'),
        max_length=6,
    )
    dst = models.BooleanField(
        _('Daylight saving time'),
    )
    in_current_country = models.BooleanField(
        _('Is in current country'),
    )
    in_eu = models.BooleanField(
        _('Is in EU'),
    )
    economic_group = models.CharField(
        _('Economic group'),
        max_length=100,
        null=True,
    )
    state = models.ForeignKey(
        'location.State',
        null=True,
        on_delete=models.CASCADE,
    )
    has_airport = models.BooleanField(
        _('Has airport?'),
    )
    has_border_crossing = models.BooleanField(
        _('Has border crossing?'),
        default=False,
    )
    has_customs_lodge = models.BooleanField(
        _('Has customs lodge?'),
        default=False,
    )
    discharge = models.BooleanField(
        _('Discharge'),
        default=False,
    )
    has_outport = models.BooleanField(
        _('Has outport?'),
        default=False,
    )
    has_post = models.BooleanField(
        _('Has post?'),
        default=False,
    )
    has_rail = models.BooleanField(
        _('Has rail?'),
        default=False,
    )
    has_road = models.BooleanField(
        _('Has road?'),
    )
    has_seaport = models.BooleanField(
        _('Has seaport?'),
    )
    has_store = models.BooleanField(
        _('Has store?'),
        default=False,
    )
    has_terminal = models.BooleanField(
        _('Has terminal?'),
        default=False,
    )
    has_unload = models.BooleanField(
        _('Has unload?'),
        default=False,
    )
    name_with_dicriticals = models.CharField(
        _('Name with diacriticals'),
        max_length=100,
    )
    is_active = models.BooleanField(
        _('Port is active'),
        default=True,
    )

    def __str__(self):
        return f'Port {self.code}, {self.name}'
