import logging
from django.template.loader import get_template

from config.celery import celery_app
from django.core.mail import send_mail
from django.conf import settings

from app.handling.models import LocalFee, ShippingMode
from config.settings.local import DOMAIN_ADDRESS

from django.utils.translation import ugettext as _

logger = logging.getLogger("acemaven.task.logging")


@celery_app.task
def send_registration_email(token, recipient_email):
    subject = _('Acemaven. Registration process.')
    logger.info(f'New registration email is going to be send to {recipient_email}')
    message_body = f'{DOMAIN_ADDRESS}create-account?token={token}'
    template_html = get_template(f"core/emails_templates/index.html")
    text = _("To complete your sign-up, please press the button:")
    context = {
        "email": recipient_email,
        "text": text,
        "link": message_body,
        }
    message_html = template_html.render(context)
    logger.debug(f"sending invitation email to {recipient_email}")
    send_mail(subject, message_body, settings.EMAIL_HOST_USER, [recipient_email], html_message=message_html)
    logger.info(f"invitation has been sent to {recipient_email} from {settings.EMAIL_HOST_USER}")


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
