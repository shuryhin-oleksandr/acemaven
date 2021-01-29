from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from app.websockets.models import Notification
from app.websockets.tasks import send_notification


# Notification signal
@receiver(m2m_changed, sender=Notification.users.through)
def send_notification_to_user(sender, instance, action, *args, **kwargs):
    if action == 'post_add':
        send_notification.delay(instance.id)
