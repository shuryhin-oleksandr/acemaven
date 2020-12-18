import datetime
import logging
import requests

from config.celery import celery_app
from django.db.models import Q

from app.booking.models import Quote
from app.handling.models import ClientPlatformSetting, AirTrackingSetting

logger = logging.getLogger("acemaven.task.logging")


@celery_app.task(name='archive_quotes')
def daily_archive_expired_quotes():
    settings_days_limit = ClientPlatformSetting.load().number_of_days
    now_date = datetime.datetime.now().date()
    Quote.objects.filter(
        Q(
            date_created__lt=now_date - datetime.timedelta(days=settings_days_limit),
            date_to__lt=now_date - datetime.timedelta(days=14),
            _connector=Q.OR,
        ),
        is_archived=False,
    ).update(is_archived=True)


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
