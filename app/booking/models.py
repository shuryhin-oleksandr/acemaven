from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __


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
        verbose_name=_("Carrier")
    )
    direction = models.CharField(
        _('Surcharge direction, whether import or export'),
        max_length=6,
        choices=DIRECTION_CHOICES,
    )
    location = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        verbose_name=_("Location")
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
    is_archived = models.BooleanField(
        _('Surcharge is archived'),
        default=False,
    )
    shipping_mode = models.ForeignKey(
        'handling.ShippingMode',
        on_delete=models.CASCADE,
        related_name='surcharges',
        verbose_name=_("Shipping mode")
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='surcharges',
        verbose_name=_("Company")
    )
    container_types = models.ManyToManyField(
        'handling.ContainerType',
        related_name='surcharges',
        through='UsageFee',
        verbose_name=_("Container types")
    )
    additional_surcharges = models.ManyToManyField(
        'AdditionalSurcharge',
        related_name='surcharges',
        through='Charge',
    )

    def __str__(self):
        return __('Surcharge for {direction}, {location}, {expiration_date}')\
                .format(direction=self.direction,
                        location=self.location,
                        expiration_date=self.expiration_date)

    class Meta:
        verbose_name = _("Surcharge")
        verbose_name_plural = _("Surcharges")


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

    class Meta:
        verbose_name = _("Usage fee")
        verbose_name_plural = _("Usage fees")


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

    class Meta:
        verbose_name = _("Charge")
        verbose_name_plural = _("Charges")


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
        verbose_name=_("Shipping mode")
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

    class Meta:
        verbose_name = _("Additional surcharge")
        verbose_name_plural = _("Additional surcharges")


class FreightRate(models.Model):
    """
    Freight rate model.
    """

    carrier = models.ForeignKey(
        'handling.Carrier',
        on_delete=models.CASCADE,
        related_name='freight_rates',
        verbose_name=_("Carrier")
    )
    carrier_disclosure = models.BooleanField(
        _('Whether carrier name disclosed or not'),
        default=False,
    )
    origin = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        related_name='origin_freight_rates',
        verbose_name=_("Origin")
    )
    destination = models.ForeignKey(
        'handling.Port',
        on_delete=models.CASCADE,
        related_name='destination_freight_rates',
        verbose_name=_("Destination")
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
        _('Paid Booking'),
        default=False,
    )
    is_archived = models.BooleanField(
        _('Freight rate is archived'),
        default=False,
    )
    shipping_mode = models.ForeignKey(
        'handling.ShippingMode',
        on_delete=models.CASCADE,
        related_name='freight_rates',
        verbose_name=_("Shipping mode")
    )
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='freight_rates',
        verbose_name=_("Company")
    )

    def __str__(self):
        return f'{self.id}'

    class Meta:
        verbose_name = _("Freight rate")
        verbose_name_plural = _("Freight rates")


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

    class Meta:
        verbose_name = _("Rate")
        verbose_name_plural = _("Rates")


class Booking(models.Model):
    """
    Model for booking instance.
    """

    CHANGE_REQUESTED = 'change_requested'
    CHANGE_CONFIRMED = 'change_confirmed'
    CHANGE_REQUESTED_CHOICES = (
        (CHANGE_REQUESTED, 'Booking Change Requested'),
        (CHANGE_CONFIRMED, 'Booking Change Confirmed'),
    )

    DISCARDED = 'discarded'
    CONFIRMED = 'confirmed'
    ACCEPTED = 'accepted'
    REQUEST_RECEIVED = 'received'
    PENDING = 'pending'
    REJECTED = 'rejected'
    CANCELED_BY_AGENT = 'canceled_by_agent'
    CANCELED_BY_CLIENT = 'canceled_by_client'
    CANCELED_BY_SYSTEM = 'canceled_by_system'
    COMPLETED = 'completed'
    STATUS_CHOICES = (
        (PENDING, 'Booking Fee Pending'),
        (REQUEST_RECEIVED, 'Booking Request Received'),
        (ACCEPTED, 'Booking Request in Progress'),
        (CONFIRMED, 'Booking Confirmed'),
        (REJECTED, 'Booking Request Rejected'),
        (CANCELED_BY_AGENT, 'Operation Canceled by Agent'),
        (CANCELED_BY_CLIENT, 'Operation Canceled by Client'),
        (CANCELED_BY_SYSTEM, 'Operation Canceled by the System'),
        (COMPLETED, 'Operation Complete'),
        (DISCARDED, 'Booking Request Unpaid and Discarded'),
    )

    aceid = models.CharField(
        _('Booking ACEID number'),
        max_length=8,
        null=True,
    )
    date_from = models.DateField(
        _('Booking date from'),
    )
    date_to = models.DateField(
        _('Booking date to'),
    )
    payment_due_by = models.DateField(
        _('Payment due by date'),
        null=True,
    )
    is_paid = models.BooleanField(
        _('Whether booking paid or not'),
        default=False,
    )
    is_assigned = models.BooleanField(
        _('Is assigned to user'),
        default=False,
    )
    change_request_status = models.CharField(
        _('Booking change request status'),
        max_length=30,
        choices=CHANGE_REQUESTED_CHOICES,
        null=True,
    )
    status = models.CharField(
        _('Booking confirmed or not'),
        max_length=30,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    client_contact_person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='client_bookings',
        null=True,
        verbose_name=_('Client contact person')
    )
    agent_contact_person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='agent_bookings',
        null=True,
        verbose_name=_('Agent contact person')
    )
    release_type = models.ForeignKey(
        'handling.ReleaseType',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Release type')
    )
    number_of_documents = models.PositiveIntegerField(
        _('Number of documents for chosen release type'),
        validators=[MinValueValidator(1)],
        null=True,
    )
    charges = models.JSONField(
        _('Charges calculations'),
        null=True,
    )
    automatic_tracking = models.BooleanField(
        _('Automatic status tracking'),
        default=False,
    )
    vessel_arrived = models.BooleanField(
        _('Vessel arrived status'),
        default=False,
    )
    date_created = models.DateField(
        _('Date booking created'),
        auto_now_add=True,
    )
    date_accepted_by_agent = models.DateTimeField(
        _('Date booking accepted by an agent'),
        null=True,
    )
    freight_rate = models.ForeignKey(
        'FreightRate',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('Freight rate')
    )
    shipper = models.ForeignKey(
        'core.Shipper',
        on_delete=models.SET_NULL,
        related_name='bookings',
        null=True,
        verbose_name=_('Shipper')
    )
    original_booking = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='change_requests',
        null=True,
    )

    def __str__(self):
        return __('Booking [{aceid}] of freight rate [{freight_rate}].')\
                  .format(aceid=self.aceid, freight_rate=self.freight_rate.id)

    @property
    def shipping_type(self):
        return self.freight_rate.shipping_mode.shipping_type.title

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")


class CancellationReason(models.Model):
    """
    Model to save cancellation reason and comments.
    """
    CONTRACT_EXPIRED = 'expired'
    RATE_INCREASED = 'increased'
    CANNOT_MEET_DATES = 'dates'
    CLIENT_REQUESTED = 'client_requested'
    OTHER = 'other'
    REASON_CHOICES = (
        (CONTRACT_EXPIRED, 'Freight contract has expired.'),
        (RATE_INCREASED, 'Rate has been increased by Carrier.'),
        (CANNOT_MEET_DATES, 'We cannot meet the dates requested by the client or there was no space availability for '
                            'this shipment.'),
        (CLIENT_REQUESTED, 'Client requested the cancellation.'),
        (OTHER, 'Other'),
    )

    reason = models.CharField(
        _('Cancellation reason'),
        max_length=20,
        choices=REASON_CHOICES,
        null=True,
    )
    comment = models.TextField(
        _('Comment to cancellation reason'),
        null=True,
    )
    date = models.DateField(
        _('Date reason created'),
        auto_now_add=True,
    )
    agent_contact_person = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )
    booking = models.ForeignKey(
        'Booking',
        related_name='reasons',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Cancellation reason")
        verbose_name_plural = _("Cancellation reasons")


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
        verbose_name=_('Container type')
    )
    packaging_type = models.ForeignKey(
        'handling.PackagingType',
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('Packaging type')
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
        verbose_name=_('Booking')
    )
    quote = models.ForeignKey(
        'Quote',
        on_delete=models.CASCADE,
        related_name='quote_cargo_groups',
        null=True,
        verbose_name=_('Quote')
    )

    def __str__(self):
        return __('Cargo group [{id}] of booking [{booking_number}]').format(id=self.id, booking_number=self.booking.aceid)

    class Meta:
        verbose_name = _("Cargo group")
        verbose_name_plural = _("Cargo groups")


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
    is_archived = models.BooleanField(
        _('Quote is archived'),
        default=False,
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

    class Meta:
        verbose_name = _("Quote")
        verbose_name_plural = _("Quotes")


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
    charges = models.JSONField(
        _('Charges calculations'),
        null=True,
    )

    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")


class ShipmentDetails(models.Model):
    """
    Shipment details model.
    """

    booking_number = models.CharField(
        _('Booking number'),
        max_length=20,
    )
    booking_number_with_carrier = models.CharField(
        _('Booking number with carrier'),
        max_length=30,
        null=True,
    )
    flight_number = models.CharField(
        _('Flight number'),
        max_length=30,
        null=True,
    )
    vessel = models.CharField(
        _('Vessel number'),
        max_length=30,
        null=True,
    )
    voyage = models.CharField(
        _('Voyage number'),
        max_length=30,
        null=True,
    )
    container_number = models.CharField(
        _('Container number'),
        max_length=30,
        null=True,
    )
    mawb = models.CharField(
        _('MAWB'),
        max_length=30,
        null=True,
    )
    date_of_departure = models.DateTimeField(
        _('Estimated time of departure'),
    )
    date_of_arrival = models.DateTimeField(
        _('Estimated time of arrival'),
    )
    actual_date_of_departure = models.DateTimeField(
        _('Actual time of departure'),
        null=True,
    )
    actual_date_of_arrival = models.DateTimeField(
        _('Actual time of arrival'),
        null=True,
    )
    document_cut_off_date = models.DateTimeField(
        _('Document cut off date'),
        null=True,
    )
    cargo_cut_off_date = models.DateTimeField(
        _('Cargo cut off date'),
        null=True,
    )
    cargo_pick_up_location = models.CharField(
        _('Cargo pick up location'),
        max_length=100,
        null=True,
    )
    cargo_pick_up_location_address = models.CharField(
        _('Cargo pick up location address'),
        max_length=200,
        null=True,
    )
    cargo_drop_off_location = models.CharField(
        _('Cargo drop off location'),
        max_length=100,
        null=True,
    )
    cargo_drop_off_location_address = models.CharField(
        _('Cargo drop off location address'),
        max_length=200,
        null=True,
    )
    empty_pick_up_location = models.CharField(
        _('Empty pick up location'),
        max_length=100,
        null=True,
    )
    empty_pick_up_location_address = models.CharField(
        _('Empty pick up location address'),
        max_length=200,
        null=True,
    )
    container_free_time = models.PositiveIntegerField(
        _('Container free time'),
        null=True,
    )
    booking_notes = models.TextField(
        _('Booking notes'),
        null=True,
    )
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.SET_NULL,
        related_name='shipment_details',
        null=True,
    )

    def __str__(self):
        return f'{self.id}'

    class Meta:
        verbose_name = _("Shipment detail")
        verbose_name_plural = _("Shipment details")


class Transaction(models.Model):
    """
    Transaction model.
    """

    OPENED = 'opened'
    FINISHED = 'finished'
    CANCELED = 'canceled'
    EXPIRED = 'expired'
    STATUS_CHOICES = (
        (OPENED, 'Transaction opened'),
        (FINISHED, 'Transaction finished'),
        (CANCELED, 'Transaction canceled'),
        (EXPIRED, 'Transaction expired'),
    )

    txid = models.CharField(
        _('Transaction identifier'),
        max_length=35,
    )
    status = models.CharField(
        _('Transaction status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=OPENED,
    )
    charge = models.DecimalField(
        _('Transaction charge amount'),
        max_digits=15,
        decimal_places=2,
    )
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        verbose_name=_('Booking'),
    )
    qr_code = models.CharField(
        _('QR code '),
        max_length=200,
        null=True,
    )
    response = models.JSONField(
        _('Response from getting payment'),
        null=True,
    )

    def __str__(self):
        return __('{id}').format(id=self.id)

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class PaymentData(models.Model):
    """
    Model to save pix api callback data.
    """

    data = models.JSONField(
        _('Json data'),
    )


class Track(models.Model):
    """
    Model for tracking json.
    """

    date_created = models.DateTimeField(
        _('Date the track object created'),
        auto_now_add=True,
    )
    data = models.JSONField(
        _('Json data from tracking api'),
        null=True,
    )
    route = models.JSONField(
        _('Json route data from tracking api'),
        null=True,
    )
    comment = models.TextField(
        _('Comment text'),
        null=True,
    )
    manual = models.BooleanField(
        _('Manually created tracking event'),
        default=False,
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )
    status = models.ForeignKey(
        'TrackStatus',
        on_delete=models.SET_NULL,
        null=True,
    )
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='tracking',
        null=True,
    )

    class Meta:
        ordering = ('-date_created',)
        verbose_name = _("Track")
        verbose_name_plural = _("Tracks")


class TrackStatus(models.Model):
    """
    Tracking status model.
    """

    title = models.CharField(
        _('Status title'),
        max_length=256,
    )
    shipping_mode = models.ManyToManyField(
        'handling.ShippingMode',
        related_name='tracking_statuses',
        verbose_name=_("Shipping mode")
    )
    direction = models.ManyToManyField(
        'Direction',
        verbose_name=_("Direction"),
    )
    must_update_actual_date_of_departure = models.BooleanField(
        _('Must update actual date of departure'),
        default=False,
    )
    show_after_departure = models.BooleanField(
        _('Show status after actual date of departure set'),
        default=False,
    )
    auto_add_on_actual_date_of_departure = models.BooleanField(
        _('Add the status after adding actual date of departure'),
        default=False,
    )
    auto_add_on_actual_date_of_arrival = models.BooleanField(
        _('Add the status after adding actual date of arrival'),
        default=False,
    )
    auto_add_on_shipment_details_change = models.BooleanField(
        _('Add the status after changing shipment details'),
        default=False,
    )

    class Meta:
        verbose_name = _("Tracking milestone")
        verbose_name_plural = _("Tracking milestones")


class Direction(models.Model):
    """
    Export/import direction model.
    """

    title = models.CharField(
        _('Direction title'),
        max_length=6,
    )

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = _("Direction")
        verbose_name_plural = _("Directions")
