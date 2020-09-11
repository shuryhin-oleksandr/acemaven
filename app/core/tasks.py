from config.celery import celery_app
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger("jettpro.task.logging")

@celery_app.task
def send_registration_email(token, recipient_email):
    logger.info(f'New registration email going to be send to {recipient_email}')
    message_body = f'{settings.DOMAIN_ADDRESS}signup?token={token}'
    send_mail('Acemaven. Registration process.', message_body, settings.DEFAULT_FROM_EMAIL, [recipient_email])
