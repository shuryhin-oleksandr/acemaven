from django_with_extra_context_admin.admin import DjangoWithExtraContextAdmin

from app.booking.models import Surcharge, AdditionalSurcharge, FreightRate, TrackStatus, Direction, Booking, \
    CargoGroup, ShipmentDetails

import logging

from django.contrib import admin

logger = logging.getLogger(__name__)


class ShipmentDetailsInline(admin.StackedInline):
    model = ShipmentDetails
    extra = 0


class CargoGroupInline(admin.StackedInline):
    model = CargoGroup
    extra = 0


@admin.register(AdditionalSurcharge)
class AdditionalSurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(FreightRate)
class FreightRateAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(DjangoWithExtraContextAdmin, admin.ModelAdmin):
    search_fields = ('aceid',)
    django_with_extra_context_admin_view_name = False
    inlines = (ShipmentDetailsInline, CargoGroupInline,)
    readonly_fields = ('date_created', 'date_accepted_by_agent',)
    change_form_template = 'booking/booking_changeform.html'
    list_display = (
        'aceid',
        'route',
        'volume',
        'dates',
        'carrier',
        'status',
        'agent_contact_person'
    )

    fieldsets = (
        ('Operation info', {
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
        ('Dates info', {
            'fields': (
                'date_from',
                'date_to',
                'date_created',
                'date_accepted_by_agent',
            )
        }),
        (
            'General information', {
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

    def get_extra_context(self, request, **kwargs):
        extra_context = super().get_extra_context(request, **kwargs) or {}
        if 'object_id' in kwargs.keys():
            booking = Booking.objects.filter(id=kwargs['object_id']).values_list('charges', flat=True).first()
            extra_context.update({
                'total_surcharge': booking['total_surcharge'],
                'totals': booking['totals'],
                'total_freight_rate': booking['total_freight_rate'],
                'doc_fee': booking['doc_fee'],
            })
        return extra_context


@admin.register(TrackStatus)
class TrackStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('title',)
