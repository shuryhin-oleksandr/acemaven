from config.celery import celery_app
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger("jettpro.task.logging")

@celery_app.task
def send_registration_email(message_body, recipient_email):
    logger.info(f"[TASK] [EMAIL] going to send email []")

    send_mail('Acemaven. Registration process.', message_body, settings.DEFAULT_FROM_EMAIL, [recipient_email])
