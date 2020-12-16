import logging
from config.celery import celery_app
from django.core.mail import send_mail
from django.conf import settings

from app.handling.models import LocalFee, ShippingMode

logger = logging.getLogger("acemaven.task.logging")


@celery_app.task
def send_registration_email(token, recipient_email):
    subject = 'Acemaven. Registration process.'
    logger.info(f'New registration email is going to be send to {recipient_email}')
    message_body = f'{settings.DOMAIN_ADDRESS}signup?token={token}'
    send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [recipient_email])


@celery_app.task
def create_company_empty_fees(company_id):
    logger.info(f'New empty fees are going to be created for company {company_id}')
    new_fees = [
        {
            'fee_type': value_type[0],
            'company_id': company_id,
            'shipping_mode': shipping_mode,
            'value_type': LocalFee.PERCENT if value_type[0] in (LocalFee.CANCELLATION_PENALTY, LocalFee.AGENT_BOOKING)
            else LocalFee.FIXED,
        }
        for value_type in LocalFee.FEE_TYPE_CHOICES
        for shipping_mode in ShippingMode.objects.all()
    ]
    new_fees_objects = [LocalFee(**field) for field in new_fees]
    LocalFee.objects.bulk_create(new_fees_objects)
