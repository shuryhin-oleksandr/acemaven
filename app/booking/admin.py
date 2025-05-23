from django.shortcuts import redirect
from django.urls import reverse_lazy
from django_with_extra_context_admin.admin import DjangoWithExtraContextAdmin

from app.booking.models import Surcharge, AdditionalSurcharge, FreightRate, TrackStatus, Direction, Booking, \
    CargoGroup, ShipmentDetails, Transaction

from django.utils.translation import ugettext_lazy as _

import logging

from django.contrib import admin

from app.websockets.models import Chat

logger = logging.getLogger(__name__)


class ShipmentDetailsInline(admin.StackedInline):
    model = ShipmentDetails
    extra = 0
    readonly_fields = ['booking_number', 'booking_number', 'flight_number', 'vessel', 'voyage', 'container_number',
                       'mawb', 'date_of_departure', 'date_of_arrival', 'actual_date_of_departure',
                       'actual_date_of_arrival', 'document_cut_off_date', 'cargo_cut_off_date',
                       'cargo_pick_up_location', 'cargo_pick_up_location_address', 'cargo_drop_off_location',
                       'cargo_drop_off_location_address', 'empty_pick_up_location', 'empty_pick_up_location_address',
                       'container_free_time', 'booking_notes', 'booking']


class CargoGroupInline(admin.StackedInline):
    model = CargoGroup
    extra = 0
    readonly_fields = ['container_type', 'packaging_type', 'weight_measurement', 'length_measurement',
                       'volume', 'height', 'length', 'width', 'weight', 'total_wm', 'dangerous', 'frozen',
                       'description', 'booking', 'quote']


@admin.register(AdditionalSurcharge)
class AdditionalSurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(FreightRate)
class FreightRateAdmin(admin.ModelAdmin):
    pass


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction',
        'booking_number',
        'status_choices',
    )
    readonly_fields = ('response', 'booking', 'charge', 'txid', 'qr_code')

    def booking_number(self, obj):
        return obj.booking.aceid

    def transaction(self, obj):
        if obj.txid:
            number = obj.txid
        else:
            number = obj.id
        return _('Transaction number: {number}').format(number=number)

    def get_readonly_fields(self, request, obj=None):
        if 'add' in request.META['PATH_INFO']:
            return ()
        else:
            return self.readonly_fields

    def status_choices(self, obj):
        choice = \
            next(filter(lambda x: x[0] == obj.status, Transaction.STATUS_CHOICES),
                 Transaction.STATUS_CHOICES[0])[1]
        return _(choice)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "status":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in Transaction.STATUS_CHOICES]

        return super(TransactionAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    status_choices.short_description = _("Status")
    transaction.short_description = _("Transaction")
    booking_number.short_description = _("Booking number")


class TransactionInline(admin.StackedInline):
    model = Transaction
    extra = 0
    readonly_fields = ['txid', 'charge', 'booking', 'qr_code', 'response']

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "status":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in Transaction.STATUS_CHOICES]

        return super(TransactionInline, self).formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(Booking)
class BookingAdmin(DjangoWithExtraContextAdmin, admin.ModelAdmin):
    search_fields = ('aceid',)
    django_with_extra_context_admin_view_name = False
    inlines = (ShipmentDetailsInline, CargoGroupInline, TransactionInline)
    readonly_fields = ('date_created', 'date_accepted_by_agent', 'aceid', 'date_from', 'date_to',
                       'payment_due_by', 'client_contact_person', 'agent_contact_person',
                       'release_type', 'number_of_documents', 'automatic_tracking', 'vessel_arrived',
                       'freight_rate', 'shipper', 'original_booking')
    change_form_template = 'booking/booking_changeform.html'
    list_display = (
        'aceid',
        'route',
        'volume',
        'dates',
        'carrier',
        'status_choice',
        'agent_contact_person'
    )

    fieldsets = (
        (_('Operation info'), {
            'fields': (
                'aceid',
                'status',
                'change_request_status',
                'is_assigned',
                'is_paid',
                'payment_due_by',
            ),
        }
         ),
        (_('Dates info'), {
            'fields': (
                'date_from',
                'date_to',
                'date_accepted_by_agent',
            )
        }),
        (
            _('General information'), {
                'fields':
                    (
                        'client_contact_person',
                        'agent_contact_person',
                        'release_type',
                        'number_of_documents',
                        'automatic_tracking',
                        'vessel_arrived',
                        'freight_rate',
                        'shipper',
                    )
            }
        )
    )

    def route(self, obj):
        origin = obj.freight_rate.origin.code
        destination = obj.freight_rate.destination.code
        return f'{origin} {destination}'

    def volume(self, obj):
        volumes = obj.cargo_groups.values_list('volume', 'container_type__code').all()
        return [(f'{volume[0]} * {volume[1]} ') for volume in volumes]

    def dates(self, obj):
        return f'{obj.date_from} – {obj.date_to}'

    def carrier(self, obj):
        return obj.freight_rate.carrier.title

    def chat(self, obj):
        return Chat.objects.filter(operation=obj)

    def messages(self, obj):
        chat = Chat.objects.filter(operation=obj).order_by('chat_messages__date_created') \
            .values_list('chat_messages__user__email',
                         'chat_messages__text',
                         'chat_messages__date_created', )
        return chat

    def get_readonly_fields(self, request, obj=None):
        if 'add' in request.META['PATH_INFO']:
            return ()
        else:
            return self.readonly_fields

    def get_extra_context(self, request, **kwargs):
        extra_context = super().get_extra_context(request, **kwargs) or {}
        if 'object_id' in kwargs.keys():
            if kwargs['object_id']:
                booking = Booking.objects.filter(id=kwargs['object_id']).values_list('charges', flat=True).first()
                extra_context.update({
                    'total_surcharge': booking['total_surcharge'],
                    'totals': booking['totals'],
                    'total_freight_rate': booking['total_freight_rate'],
                    'doc_fee': booking['doc_fee'],
                    'messages': self.messages(kwargs['object_id']),
                    'chat': self.chat(kwargs['object_id']) if self.chat(kwargs['object_id']) else None
                })
        return extra_context

    def response_change(self, request, obj):
        if "_open_chat" in request.POST:
            chat = Chat.objects.filter(operation=obj.id).first()
            user = request.user
            chat.users.add(user)
            url = reverse_lazy("booking:operation-chat", kwargs=dict(booking=obj.id, chat_id=chat.id))
            return redirect(url)
        return super().response_change(request, obj)

    def formfield_for_choice_field(self, db_field, request, **kwargs):

        if db_field.name == "status":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in Booking.STATUS_CHOICES]

        if db_field.name == "change_request_status":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in Booking.CHANGE_REQUESTED_CHOICES]

        return super(BookingAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    def status_choice(self, obj):
        choice = \
            next(filter(lambda x: x[0] == obj.status, Booking.CHANGE_REQUESTED_CHOICES), Booking.CHANGE_REQUESTED_CHOICES[0])[1]
        return _(choice)

    status_choice.short_description = _("Status")
    route.short_description = _("Route")
    volume.short_description = _("Volume")
    dates.short_description = _("Dates")
    carrier.short_description = _("Carrier")
    chat.short_description = _("Chat")
    messages.short_description = _("Messages")


@admin.register(TrackStatus)
class TrackStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('title',)
