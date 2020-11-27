import datetime
from config.celery import celery_app
from django.db.models import Q

from app.booking.models import Quote
from app.handling.models import ClientPlatformSetting


@celery_app.task(name='archive_quotes')
def archive_expired_quotes():
    settings_days_limit = ClientPlatformSetting.objects.first().number_of_days
    now_date = datetime.datetime.now().date()
    Quote.objects.filter(
        Q(
            date_created__lt=now_date - datetime.timedelta(days=settings_days_limit),
            date_to__lt=now_date - datetime.timedelta(days=14),
            _connector=Q.OR,
        ),
        is_archived=False,
    ).update(is_archived=True)
