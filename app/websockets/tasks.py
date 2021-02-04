import datetime
import logging

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from app.websockets.utils import notification_to_json
from config.celery import celery_app

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from app.booking.models import Booking
from app.websockets.models import Chat, Notification

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
def create_and_assign_notification(section, text, users_ids, action_path, object_id=None):
    notification = Notification.objects.create(
        section=section,
        text=text,
        action_path=action_path,
        object_id=object_id,
    )
    users = User.objects.filter(id__in=users_ids)
    notification.users.set(users)


@celery_app.task(name='send_notification')
def send_notification(notification_id):
    channel_layer = get_channel_layer()

    notification = Notification.objects.filter(id=notification_id).first()
    if notification:
        data = notification_to_json(notification)
        for user in notification.users.all():
            async_to_sync(channel_layer.group_send)(
                f'{user.id}',
                {
                    'type': 'notify',
                    'data': {
                        'command': 'notification',
                        'notification': data,
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
    notifications.update(object_id=new_operation_id)

    channel_layer = get_channel_layer()
    users_ids = list(set(notifications.values_list('users__id', flat=True)))
    for user_id in users_ids:
        async_to_sync(channel_layer.group_send)(
            f'{user_id}',
            {
                'type': 'fetch_notifications',
            },
        )
