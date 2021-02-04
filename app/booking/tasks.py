import datetime
import logging
import requests

from config.celery import celery_app
from django.db.models import Q, Case, When, Value, CharField
from django.utils import timezone

from app.booking.models import Quote, Booking, Track, CancellationReason, Surcharge, FreightRate, ShipmentDetails
from app.booking.utils import sea_event_codes
from app.handling.models import ClientPlatformSetting, AirTrackingSetting, SeaTrackingSetting, GeneralSetting
from app.location.models import Country
from app.websockets.tasks import create_and_assign_notification
from app.websockets.models import Notification

logger = logging.getLogger("acemaven.task.logging")

main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


@celery_app.task(name='archive_quotes')
def daily_archive_expired_quotes():
    settings_days_limit = ClientPlatformSetting.load().number_of_days
    now_date = timezone.localtime().date()
    Quote.objects.filter(
        Q(
            date_created__lt=now_date - datetime.timedelta(days=settings_days_limit),
            date_to__lt=now_date - datetime.timedelta(days=14),
            _connector=Q.OR,
        ),
        is_archived=False,
    ).update(is_archived=True)


@celery_app.task(name='discard_unpaid_bookings')
def daily_discard_unpaid_client_bookings():
    settings_days_limit = GeneralSetting.load().number_of_days_request_can_stay
    now_date = timezone.localtime().date()
    Booking.objects.filter(
        status=Booking.PENDING,
        date_created__lt=now_date - datetime.timedelta(days=settings_days_limit),
        is_paid=False,
    ).update(status=Booking.DISCARDED)


@celery_app.task(name='cancel_unconfirmed_bookings')
def daily_cancel_unconfirmed_agent_bookings():
    settings = GeneralSetting.load()
    now_date = timezone.localtime().date()
    queryset = Booking.objects.filter(
        status=Booking.ACCEPTED,
    ).annotate(
        direction=Case(When(freight_rate__origin__code__startswith=MAIN_COUNTRY_CODE, then=Value('export')),
                       default=Value('import'),
                       output_field=CharField(),
                       )
    ).filter(Q(
        Q(
            direction='export',
            date_accepted_by_agent__lt=now_date - datetime.timedelta(days=settings.export_deadline_days),
        ),
        Q(
            direction='import',
            date_accepted_by_agent__lt=now_date - datetime.timedelta(days=settings.import_deadline_days),
        ),
        _connector=Q.OR,
    ))
    queryset.update(status=Booking.CANCELED_BY_SYSTEM)
    for operation in queryset:
        CancellationReason.objects.create(
            reason=CancellationReason.OTHER,
            comment='Operation cancelled according to expired time for confirming booking by an agent',
            booking=operation,
        )


@celery_app.task(name='post_awb_number')
def send_awb_number_to_air_tracking_api(booking_number):
    logger.info(f'Sending new airway bill number to track [{booking_number}]')
    settings = AirTrackingSetting.load()
    url = settings.url
    headers = {
        'Password': settings.password,
        'User': settings.user,
    }
    data = {
        "waybillIdentification": [booking_number],
        "notifyAddressType": "PIMA",
        "notifyAddress": settings.pima,
    }
    response = requests.post(url, json=data, headers=headers)
    logger.info(f'Response text for airway bill number [{booking_number}] - {response.text}')


@celery_app.task(name='track_sea_operations')
def track_confirmed_sea_operations():
    logger.info(f'Starting to get track statuses for confirmed operations')
    settings = SeaTrackingSetting.load()
    url = settings.url
    api_key = settings.api_key
    operations = Booking.objects.filter(
        status=Booking.CONFIRMED,
        freight_rate__shipping_mode__shipping_type__title='sea',
        automatic_tracking=True,
        vessel_arrived=False,
        original_booking__isnull=True,
    )
    for operation in operations:
        direction = 'export' if operation.freight_rate.origin.code.startswith(MAIN_COUNTRY_CODE) else 'import'
        booking_number = operation.shipment_details.first().booking_number
        scac = operation.freight_rate.carrier.scac
        base_url = f'?type=BK&number={booking_number}&sealine={scac}&api_key={api_key}'
        data_url = f'{url}reference{base_url}'
        route_url = f'{url}route{base_url}'

        data_response = requests.get(data_url)
        data_json = data_response.json() if (data_status_code := data_response.status_code) == 200 \
            else {
            'status': 'error',
            'message': f'Status code - {data_status_code}',
        }

        if data_json.get('status') == 'error':
            if (message := data_json.get('message')) == 'WRONG_NUMBER':
                create_and_assign_notification.delay(
                    Notification.OPERATIONS,
                    f'The shipment {operation.aceid} cannot be tracked because of wrong booking number.',
                    [operation.agent_contact_person_id, ],
                    Notification.OPERATION,
                    object_id=operation.id,
                )
            else:
                pass
                # Add notification to acemaven platform
            break

        shipment_details = operation.shipment_details.first()

        if 'containers' in data_json['data']:
            for container in data_json['data']['containers']:
                for event in container['events']:
                    status = event.get('status', 'UNK')
                    event['status'] = sea_event_codes.get(status)
                    if status == 'VAD':
                        operation.vessel_arrived = True
                        operation.save()
                    if status == 'VDL' and not shipment_details.actual_date_of_departure:
                        shipment_details.actual_date_of_departure = timezone.localtime()
                        shipment_details.save()
                        if direction == 'import':
                            create_and_assign_notification.delay(
                                Notification.OPERATIONS_IMPORT,
                                f'The shipment {operation.aceid} has departed from {operation.freight_rate.origin}.',
                                [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                                Notification.OPERATION,
                                object_id=operation.id,
                            )
                    event['location'] = next(
                        filter(lambda x: x.get('id') == event['location'], data_json['data'].get('locations')), {}
                    ).get('name', '')
                    event['vessel'] = next(
                        filter(lambda x: x.get('id') == event['vessel'], data_json['data'].get('vessels')), {}
                    ).get('name', '')

        if 'route' in data_json['data']:
            date = data_json['data']['route'].get('postpod', {}).get('date')
            if date and not shipment_details.actual_date_of_arrival:
                shipment_details.actual_date_of_arrival = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                shipment_details.save()
                if direction == 'export':
                    create_and_assign_notification.delay(
                        Notification.OPERATIONS_EXPORT,
                        f'The shipment {operation.aceid} has arrived at {operation.freight_rate.destination}.',
                        [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                        Notification.OPERATION,
                        object_id=operation.id,
                    )

        route_response = requests.get(route_url)
        route_json = route_response.json() if (route_status_code := route_response.status_code) == 200 \
            else {
            'status': 'error',
            'message': f'Status code - {route_status_code}',
        }

        track, _ = Track.objects.get_or_create(
            manual=False,
            booking=operation,
            defaults={'booking': operation}
        )
        track.data = data_json
        track.route = route_json
        track.save()


@celery_app.task(name='notify_users_of_expiring_surcharges')
def daily_notify_users_of_expiring_surcharges():
    now_date = timezone.localtime().date()
    surcharges = Surcharge.objects.filter(
        temporary=False,
        is_archived=False,
        expiration_date=now_date + datetime.timedelta(days=5),
    )
    for surcharge in surcharges:
        users_ids = list(surcharge.company.role_set.filter(
            groups__name__in=('master', 'agent')
        ).values_list('user__id', flat=True))
        create_and_assign_notification.delay(
            Notification.SURCHARGES,
            'Surcharges are about to expire. '
            'Please, extend its expiration rate or create a new one with the updated costs.',
            users_ids,
            Notification.SURCHARGE,
            object_id=surcharge.id,
        )


@celery_app.task(name='notify_users_of_expiring_freight_rates')
def daily_notify_users_of_expiring_freight_rates():
    now_date = timezone.localtime().date()
    freight_rates = FreightRate.objects.filter(
        is_active=True,
        temporary=False,
        is_archived=False,
        rates__expiration_date=now_date + datetime.timedelta(days=5),
    ).distinct()
    for freight_rate in freight_rates:
        users_ids = list(freight_rate.company.role_set.filter(
            groups__name__in=('master', 'agent')
        ).values_list('user__id', flat=True))
        create_and_assign_notification.delay(
            Notification.FREIGHT_RATES,
            'Rates are about to expire. '
            'Please, extend its expiration rate or create a new one with the updated costs.',
            users_ids,
            Notification.FREIGHT_RATE,
            object_id=freight_rate.id,
        )


@celery_app.task(name='notify_users_of_import_sea_shipment_arrival')
def daily_notify_users_of_import_sea_shipment_arrival():
    now_date = timezone.localtime().date()
    shipment_details = ShipmentDetails.objects.annotate(
        direction=Case(When(booking__freight_rate__origin__code__startswith=MAIN_COUNTRY_CODE, then=Value('export')),
                       default=Value('import'),
                       output_field=CharField(),
                       )
    ).filter(
        direction='import',
        date_of_arrival__date=now_date + datetime.timedelta(days=3),
        booking__freight_rate__shipping_mode__shipping_type__title='sea',
    )
    for shipment_detail in shipment_details:
        booking = shipment_detail.booking
        create_and_assign_notification.delay(
            Notification.OPERATIONS_IMPORT,
            f'The shipment {booking.aceid} is set to arrive in 3 days at {booking.freight_rate.destination}.',
            [booking.agent_contact_person_id, booking.client_contact_person_id, ],
            Notification.OPERATION,
            object_id=booking.id,
        )
