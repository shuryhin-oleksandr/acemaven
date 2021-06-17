import datetime
import logging
import smtplib

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.template.loader import get_template

from app.websockets.utils import notification_to_json
from config import settings
from config.celery import celery_app

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone, translation

from app.booking.models import Booking
from app.websockets.models import Chat, Notification

from django.utils.translation import ugettext_lazy as _

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("acemaven.task.logging")
User = get_user_model()


@celery_app.task(name='create_chat_for_operation')
def create_chat_for_operation(operation_id):
    logger.info(f'Creating chat for operation [{operation_id}] and adding users to it.')
    operation = Booking.objects.filter(id=operation_id).first()
    chat = Chat.objects.create(
        operation=operation,
    )
    users = User.objects.filter(Q(
        client_bookings=operation,
        agent_bookings=operation,
        _connector=Q.OR
    ))
    chat.users.set(users)


@celery_app.task(name='create_and_assign_notification')
def create_and_assign_notification(section, text_body, text_params, users_ids, action_path, object_id=None):
    users = User.objects.filter(id__in=users_ids)

    for user in users:
        code = user.language
        translation.activate(code)
        text = _(text_body)
        if text_params:
            text = text.format(**text_params)
        translation.deactivate()

        notification = Notification.objects.create(
            section=section,
            text=text,
            action_path=action_path,
            object_id=object_id,
        )

        notification.users.add(user)
        translation.deactivate()


@celery_app.task(name='send_notification')
def send_notification(notification_id):
    channel_layer = get_channel_layer()

    notification = Notification.objects.filter(id=notification_id).first()
    if notification:
        data = notification_to_json(notification)
        for user in notification.users.all():
            logger.info(f'{user.id}{"_chat" if notification.section == Notification.CHATS else ""}')
            condition = notification.section == Notification.CHATS
            async_to_sync(channel_layer.group_send)(
                f'{user.id}{"_chat" if condition else ""}',
                {
                    'type': 'notify',
                    'data': {
                        'command': f'{"chat_" if condition else ""}notification',
                        f'{"chat_" if condition else ""}notification': data,
                    },
                },
            )
        logger.info(f'Notification [{notification_id}] with text "{notification.text}" was sent.')


@celery_app.task(name='delete_old_notifications')
def daily_delete_old_notifications():
    now_date = timezone.localtime()
    Notification.objects.filter(
        date_created__lt=now_date - datetime.timedelta(days=30),
    ).delete()


@celery_app.task(name='reassign_notifications_after_change_request_confirm')
def reassign_confirmed_operation_notifications(old_operation_id, new_operation_id):
    notifications = Notification.objects.filter(
        section=Notification.OPERATIONS,
        object_id=old_operation_id,
    )
    users_ids = list(set(notifications.values_list('users__id', flat=True)))
    notifications.update(object_id=new_operation_id)

    channel_layer = get_channel_layer()
    for user_id in users_ids:
        async_to_sync(channel_layer.group_send)(
            f'{user_id}',
            {
                'type': 'fetch_notifications',
            },
        )


@celery_app.task(name='delete_accepted_booking_notifications')
def delete_accepted_booking_notifications(booking_id):
    notifications = Notification.objects.filter(
        section=Notification.REQUESTS,
        action_path=Notification.BOOKING,
        object_id=booking_id,
    )
    users_ids = list(set(notifications.values_list('users__id', flat=True)))
    notifications.delete()

    channel_layer = get_channel_layer()
    for user_id in users_ids:
        async_to_sync(channel_layer.group_send)(
            f'{user_id}',
            {
                'type': 'fetch_notifications',
            },
        )


@celery_app.task(name='send_emails')
def send_email(text_body, text_params, users_ids, object_id=None, data=None):

    users = User.objects.filter(id__in=users_ids)

    for user in users:
        msg = MIMEMultipart('alternative')

        msg['Subject'] = 'Acemaven'
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = user.email
        code = user.language
        translation.activate(code)
        text = _(text_body)
        if text_params:
            text = text.format(**text_params)

        body_text = text

        context = {
            "person": f'{user.first_name} {user.last_name}',
            "text": text,
            "data": data,
            "link": object_id,
        }

        template_html = get_template(f"core/emails_templates/index.html")
        message_html = template_html.render(context)

        part1 = MIMEText(body_text, 'plain')
        part2 = MIMEText(message_html, 'html')

        msg.attach(part1)
        msg.attach(part2)

        mail = smtplib.SMTP("smtp.outlook.office365.com", 587, timeout=20)
        mail.starttls()
        recepient = [user.email,]

        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        logger.debug(f"sending email to {user.email}")
        mail.sendmail(settings.EMAIL_HOST_USER, recepient, msg.as_string())

        logger.debug(f"sending email to {user.email}")
        # send_mail(text, text, settings.EMAIL_HOST_USER, [user.email, ], html_message=message_html)
        logger.info(f"email has been sent to {user.email}")
        mail.quit()
        translation.deactivate()
