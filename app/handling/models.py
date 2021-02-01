from decimal import Decimal

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _


api_key_validator = RegexValidator(
    regex=r'^(\w|\d){4}-(\w|\d){4}-(\w|\d){4}-(\w|\d){4}-(\w|\d){4}$',
    message='Invalid format. Must be: 0000-0000-0000-0000',
)


class SingletonModel(models.Model):
    """Singleton Django Model"""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Save object to the database.  When you save an instance of the model,
        it always has the same primary key, so there is only one record for
        this model in the database.
        """

        self.pk = 1
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        """
        Load object from the database. if the object does not exist in a database,
        it will be created.
        """

        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class ShippingType(models.Model):
    """
    Shipping type model.
    """

    title = models.CharField(
        _('Shipping Type Title'),
        max_length=20,
    )

    def __str__(self):
        return f'{self.title}'


class ShippingMode(models.Model):
    """
    Shipping mode model.
    """

    title = models.CharField(
        _('Shipping Mode Title'),
        max_length=100,
    )
    is_need_volume = models.BooleanField(
        _('Is need volume'),
        default=False,
    )
    has_freight_containers = models.BooleanField(
        _('Has container types in freight rate'),
        default=False,
    )
    has_surcharge_containers = models.BooleanField(
        _('Has container types in surcharge'),
        default=False,
    )
    shipping_type = models.ForeignKey(
        'ShippingType',
        on_delete=models.CASCADE,
        related_name='shipping_modes',
    )

    def __str__(self):
        return f'{self.title} [{self.shipping_type}]'


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
        null=True,
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
        null=True,
    )
    weight = models.DecimalField(
        _('Weight'),
        max_digits=15,
        decimal_places=2,
    )
    weight_unit = models.CharField(
        _('Weight unit'),
        max_length=10,
        null=True,
    )
    shipping_modes = models.ManyToManyField(
        'ShippingMode',
        related_name='packaging_types',
    )

    def __str__(self):
        return f'{self.code}, {self.description}'


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
    shipping_mode = models.ForeignKey(
        'ShippingMode',
        on_delete=models.SET_NULL,
        null=True,
        related_name='container_types',
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
    is_frozen = models.BooleanField(
        _('Is frozen'),
        default=False,
    )
    can_be_dangerous = models.BooleanField(
        _('Can be dangerous'),
        default=False,
    )

    def __str__(self):
        return f'{self.code}'


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

    def __str__(self):
        return f'{self.title} [{self.code}]'


class Carrier(models.Model):
    """
    Carrier model.
    """

    title = models.CharField(
        _('Carrier title'),
        max_length=100,
    )
    scac = models.CharField(
        _('SCAC code'),
        max_length=4,
        null=True,
    )
    code = models.CharField(
        _('2 letter air code'),
        max_length=2,
        null=True,
    )
    prefix = models.CharField(
        _('Airline prefix'),
        max_length=3,
        null=True,
    )
    shipping_type = models.ForeignKey(
        'ShippingType',
        on_delete=models.CASCADE,
        related_name='carriers',
    )

    def __str__(self):
        return f'{self.title}, {self.shipping_type}'


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
    CANCELLATION_PENALTY = 'penalty'
    AGENT_BOOKING = 'agent_booking'
    SERVICE = 'service'

    FEE_TYPE_CHOICES = (
        (BOOKING, 'Booking Fee'),
        (CANCELLATION_PENALTY, 'Cancellation Penalty Fee'),
        (AGENT_BOOKING, 'Agent Booking Fee'),
        (SERVICE, 'Service Fee'),
    )

    FIXED = 'fixed'
    PERCENT = 'percent'
    VALUE_TYPE_CHOICES = (
        (FIXED, 'Fixed value'),
        (PERCENT, 'Percentage'),
    )

    fee_type = models.CharField(
        _('Fee type'),
        max_length=20,
        choices=FEE_TYPE_CHOICES,
    )
    is_active = models.BooleanField(
        _('Fee enabled'),
        default=False,
    )
    value = models.DecimalField(
        _('Fee value'),
        max_digits=15,
        decimal_places=2,
        default=0,
    )
    value_type = models.CharField(
        _('Value type'),
        max_length=10,
        choices=VALUE_TYPE_CHOICES,
        default=FIXED,
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

    def __str__(self):
        return f'{self.fee_type}'


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

    def __str__(self):
        return f'{self.fee_type}, {self.company}'


class Currency(models.Model):
    """
    Currency model.
    """

    code = models.CharField(
        _('Currency three char code'),
        max_length=3,
    )
    is_active = models.BooleanField(
        _('Is active in the platform'),
        default=False,
    )
    is_main = models.BooleanField(
        _('Is main currency in the platform'),
        default=False,
    )

    def __str__(self):
        return f'{self.code}'


class Port(gis_models.Model):
    """
    Ports and Airports model.
    """

    PORT = 'port'
    AIRPORT = 'airport'
    PORT_AIRPORT_CHOICES = (
        (PORT, 'Port'),
        (AIRPORT, 'Airport'),
    )

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
        null=True,
    )
    is_active = models.BooleanField(
        _('Port is active'),
        default=True,
    )
    port_or_airport = models.CharField(
        _('Port or airport'),
        max_length=10,
        choices=PORT_AIRPORT_CHOICES,
        default=PORT,
    )
    country = models.ForeignKey(
        'location.Country',
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('code', )

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return f'{self.code}, {self.name}, {self.code[:2]}'

    def get_lat_long_coordinates(self):
        result = dict()
        if coordinates := self.coordinates:
            result = {
                'latitude': coordinates.y,
                'longitude': coordinates.x,
            }
        return result


class ExchangeRate(models.Model):
    """
    System platform exchange rate against main currency model.
    """

    rate = models.DecimalField(
        _('Exchange rate'),
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
    )
    spread = models.DecimalField(
        _('Spread'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    currency = models.ForeignKey(
        'Currency',
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(is_active=True, is_main=False),
    )
    is_platforms = models.BooleanField(
        _('Is exchange rate of the platform'),
        default=False,
    )
    billing_exchange_rate = models.ForeignKey(
        'BillingExchangeRate',
        on_delete=models.CASCADE,
        related_name='rates',
        null=True,
    )

    def __str__(self):
        return f'Exchange rate from {self.currency.code}'


class BillingExchangeRate(models.Model):
    """
    Billing company exchange rate model.
    """

    date = models.DateField(
        _('Exchange rate date'),
        auto_now_add=True,
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='exchange_rates',
    )

    class Meta:
        ordering = ['date', ]


class ClientPlatformSetting(SingletonModel):
    """
    Client platform setting model.
    """

    number_of_results = models.PositiveIntegerField(
        _('Number of rates results will return'),
        validators=[MinValueValidator(1)],
    )
    hide_carrier_name = models.BooleanField(
        _('Hide carrier name in search results'),
        default=False,
    )
    number_of_bids = models.PositiveIntegerField(
        _('Number of bids client can receive'),
        validators=[MinValueValidator(1)],
    )
    number_of_days = models.PositiveIntegerField(
        _('Number of days a quote will be shown to ff'),
        validators=[MinValueValidator(1)],
    )
    enable_booking_fee_payment = models.BooleanField(
        _('Enable booking/service fee payment to book freight rate'),
        default=True,
    )


class GeneralSetting(SingletonModel):
    """
    General settings.
    """

    AFTER_BOOKING = 'after_booking'
    ALL = 'all'
    IN_OPERATION_PAGE = 'in_operation'
    SHOW_FREIGHT_FORWARDER_NAME_CHOICES = (
        (AFTER_BOOKING, 'Show after booking is paid'),
        (ALL, 'Show in search results and after'),
        (IN_OPERATION_PAGE, 'Show only on operation page'),
    )

    show_freight_forwarder_name = models.CharField(
        _('Hide/show freight forwarder'),
        max_length=50,
        choices=SHOW_FREIGHT_FORWARDER_NAME_CHOICES,
        default=AFTER_BOOKING,
    )
    number_of_days_request_can_stay = models.PositiveIntegerField(
        _('Number of days an unpaid booking request can stay in client list until discarded'),
        validators=[MinValueValidator(1)],
    )
    export_deadline_days = models.PositiveIntegerField(
        _('Number of days that the agent will have to confirm a booking request(export)'),
        validators=[MinValueValidator(1)],
    )
    import_deadline_days = models.PositiveIntegerField(
        _('Number of days that the agent will have to confirm a booking request(import)'),
        validators=[MinValueValidator(1)],
    )

    def __str__(self):
        return 'General platform settings'


class AirTrackingSetting(SingletonModel):
    """
    Settings of air tracking api.
    """

    url = models.CharField(
        _('Api url to track delivery progress of air shipment'),
        max_length=256,
    )
    user = models.CharField(
        _('Username credential'),
        max_length=30,
    )
    password = models.CharField(
        _('Password credential'),
        max_length=30,
    )
    pima = models.CharField(
        _('PIMA'),
        max_length=20,
    )

    def __str__(self):
        return 'Air tracking api general settings'


class SeaTrackingSetting(SingletonModel):
    """
    Settings of sea tracking api.
    """

    url = models.CharField(
        _('Api url to track delivery progress of sea shipment'),
        max_length=256,
    )
    api_key = models.CharField(
        _('Api key'),
        max_length=24,
        validators=[api_key_validator, ],
    )

    def __str__(self):
        return 'Sea tracking api general settings'


class PixApiSetting(models.Model):
    """
    Pix api setting model.
    """

    base_url = models.CharField(
        _('Pix api base url'),
        max_length=256,
    )
    token_uri = models.CharField(
        _('Pix api token uri'),
        max_length=256,
    )
    cob_uri = models.CharField(
        _('Pix api cob uri'),
        max_length=256,
    )
    client_id = models.TextField(
        _('Client id'),
    )
    client_secret = models.TextField(
        _('Client secret'),
    )
    developer_key = models.TextField(
        _('Developer key'),
    )
    basic_token = models.TextField(
        _('Basic token value'),
    )
    bank_account = models.OneToOneField(
        'core.BankAccount',
        on_delete=models.CASCADE,
        related_name='pix_api',
    )
