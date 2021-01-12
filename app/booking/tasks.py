import datetime
import logging
import requests

from config.celery import celery_app
from django.db.models import Q
from django.utils import timezone

from app.booking.models import Quote, Booking, Track
from app.booking.utils import sea_event_codes
from app.handling.models import ClientPlatformSetting, AirTrackingSetting, SeaTrackingSetting, GeneralSetting

logger = logging.getLogger("acemaven.task.logging")


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
        original_booking__isnull=True,
    )
    for operation in operations:
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
        if 'containers' in data_json['data']:
            for container in data_json.get('data').get('containers'):
                for event in container['events']:
                    event['status'] = sea_event_codes.get(event.get('status', 'UNK'))
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
