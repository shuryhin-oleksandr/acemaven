from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class Chat(models.Model):
    """
    Model for chat room.
    """

    date_created = models.DateTimeField(
        'Date chat created',
        auto_now_add=True,
    )
    operation = models.OneToOneField(
        'booking.Booking',
        on_delete=models.CASCADE,
        null=True,
    )
    users = models.ManyToManyField(
        User,
        related_name='chats',
        through='ChatPermission',
    )

    class Meta:
        ordering = ['-id', ]

    def __str__(self):
        return f'Chat [{self.id}]'


class ChatPermission(models.Model):
    """
    Through model for chat and users.
    """

    has_perm_to_read = models.BooleanField(
        _('User has permission to read messages'),
        default=True,
    )
    has_perm_to_write = models.BooleanField(
        _('User has permission to write messages'),
        default=True,
    )
    chat = models.ForeignKey(
        'Chat',
        on_delete=models.CASCADE,
        related_name='user_permissions',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_permissions',
    )

    def __str__(self):
        return f'{self.user.get_full_name()} permission for chat {self.chat_id}'


class Message(models.Model):
    """
    Model for chat message.
    """

    text = models.TextField(
        'Message',
        blank=True,
    )
    date_created = models.DateTimeField(
        'Date created',
        auto_now_add=True,
    )
    chat = models.ForeignKey(
        'Chat',
        on_delete=models.CASCADE,
        related_name='chat_messages',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_messages'
    )

    class Meta:
        ordering = ['date_created', ]

    def __str__(self):
        return f'Message [{self.id}] of chat [{self.chat_id}]'


class MessageFile(models.Model):
    """
    Model to store files for messages.
    """

    file = models.FileField(
        _('File from chat'),
        upload_to='chat_documents',
    )
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='files',
        null=True,
    )

    def __str__(self):
        return f'File of message [{self.message}]'


class Notification(models.Model):
    """
    Model for user notification.
    """
    SURCHARGES = 'surcharges'
    FREIGHT_RATES = 'freight_rates'
    REQUESTS = 'requests'
    OPERATIONS = 'operations'
    OPERATIONS_IMPORT = 'operations_import'
    OPERATIONS_EXPORT = 'operations_export'
    SECTION_CHOICES = (
        (SURCHARGES, 'Surcharges'),
        (FREIGHT_RATES, 'Freight Rates'),
        (REQUESTS, 'Requests'),
        (OPERATIONS, 'Operations'),
        (OPERATIONS_IMPORT, 'Operations (Imports)'),
        (OPERATIONS_EXPORT, 'Operations (Exports)'),
    )

    BOOKING = 'booking'
    BILLING = 'billing'
    OPERATION = 'operation'
    SURCHARGE = 'surcharge'
    FREIGHT_RATE = 'freight_rate'
    ACTION_CHOICES = (
        (BOOKING, 'Booking'),
        (BILLING, 'Billing'),
        (OPERATION, 'Operation'),
        (SURCHARGE, 'Surcharge'),
        (FREIGHT_RATE, 'Freight Rate'),
    )

    section = models.CharField(
        _('Section'),
        max_length=17,
        choices=SECTION_CHOICES,
    )
    date_created = models.DateTimeField(
        _('Date the notification object created'),
        auto_now_add=True,
    )
    text = models.TextField(
        _('Notification text'),
    )
    users = models.ManyToManyField(
        User,
        related_name='notifications',
        through='NotificationSeen',
    )
    object_id = models.PositiveIntegerField(
        _('Id of described object'),
        null=True,
    )
    action_path = models.CharField(
        _('Action path'),
        max_length=20,
        choices=ACTION_CHOICES,
        default=BOOKING,
    )

    class Meta:
        ordering = ['-date_created', ]

    def __str__(self):
        return f'Notification [{self.id}] to users {list(self.users.values_list("id", flat=True))}'

    @classmethod
    def get_section_choices_label_value(cls, value):
        return next(filter(lambda x: x[0] == value, cls.SECTION_CHOICES), cls.SECTION_CHOICES[0])[1]

    @classmethod
    def get_action_choices_label_value(cls, value):
        return next(filter(lambda x: x[0] == value, cls.ACTION_CHOICES), cls.ACTION_CHOICES[0])[1]


class NotificationSeen(models.Model):
    """
    Through model for notification and user.
    """

    notification = models.ForeignKey(
        'Notification',
        on_delete=models.CASCADE,
        related_name='users_seen',
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='notifications_seen',
    )
    is_viewed = models.BooleanField(
        _('Is seen by user'),
        default=False,
    )
