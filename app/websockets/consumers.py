import json

from urllib import parse
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q

from django.conf import settings
from django.contrib.auth import get_user_model

from app.booking.models import Booking
from app.websockets.models import Message, Chat, Notification, MessageFile, ChatPermission, Ticket
from app.websockets.tasks import create_and_assign_notification

from django.utils.translation import ugettext as _

User = get_user_model()


class ChatConsumer(WebsocketConsumer):

    def get_origin_url(self):
        headers = self.scope['headers']
        server = self.scope.get('server')

        origin = next(filter(lambda x: x[0] == b'origin', headers), [])
        origin_url = origin[1].decode() if origin else ''
        scheme = parse.urlparse(origin_url).scheme

        return f"{scheme if scheme else 'http'}://{':'.join(list(map(str, server)))}" if server else ''

    def get_full_file_url(self, file_url):
        return f'{self.get_origin_url()}{file_url}'

    @staticmethod
    def save_files(files_ids, message_id):
        MessageFile.objects.filter(id__in=files_ids).update(message_id=message_id)

    def fetch_messages(self):
        messages = Message.objects.filter(chat_id=self.chat_id)
        content = {
            'command': 'messages',
            'messages': self.messages_to_json(messages),
        }
        user = self.scope['user']
        if user_permission := user.chat_permissions.filter(chat_id=self.chat_id).first():
            if user_permission.unread_messages > 0:
                user_permission.unread_messages = 0
                user_permission.save()
        self.send_message(content)

    def new_message(self, data):
        user = self.scope['user']
        message = Message.objects.create(
            chat_id=self.chat_id,
            user=user,
            text=data['message'])
        if files_ids := data.get('files'):
            self.save_files(files_ids, message.id)
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message),
        }

        users_offline = ChatPermission.objects.filter(chat_id=self.chat_id, is_online=False)
        ticket = Ticket.objects.filter(chat_id=self.chat_id).values_list('id', flat=True).first()

        if users_offline.exists():
            for user in users_offline:
                unread_messages = user.unread_messages
                if unread_messages == 0:
                    operation_id = user.chat.operation_id
                    if operation_id:
                        aceid = Booking.objects.filter(id=user.chat.operation_id) \
                            .values_list('aceid', flat=True).first()
                        message_body = _('You have a new message in chat on operation number {aceid}') \
                            .format(aceid=aceid)
                    else:
                        topic = Ticket.objects.filter(chat_id=self.chat_id) \
                            .values_list('topic', flat=True).first()
                        message_body = _('You have a new message in support chat on topic "{topic}"') \
                            .format(topic=topic)

                        create_and_assign_notification.delay(
                            Notification.CHATS,
                            'You have a new message in support chat on topic "{topic}"',
                            {'topic':topic},
                            [user.user_id, ],
                            Notification.OPERATION if operation_id else Notification.SUPPORT,
                            object_id=operation_id if operation_id else ticket,
                        )
                unread_messages += 1
                user.unread_messages = unread_messages
                user.save()
        return self.send_chat_message(content)

    def typing_message(self, data):
        user_id = data['user_id']
        user = User.objects.filter(id=user_id).first()
        if user:
            content = {
                'command': 'typing_message',
                'user_id': user_id,
                'photo': f'{self.get_full_file_url(photo.url)}' if (photo := user.photo) else None,
            }
            return self.send_chat_message(content)

    def stop_typing_message(self, data):
        user_id = data['user_id']
        user = User.objects.filter(id=user_id).first()
        if user:
            content = {
                'command': 'stop_typing_message',
                'user_id': user_id,
            }
            return self.send_chat_message(content)

    def delete_message(self, data):
        message_id = data['message_id']
        Message.objects.filter(id=message_id).delete()
        content = {
            'command': 'delete_message',
            'message_id': message_id,
        }
        return self.send_chat_message(content)

    def file_uploading(self, data):
        message_id = data['message_id']
        content = {
            'command': 'file_uploading',
            'message_id': message_id,
        }
        return self.send_chat_message(content)

    def file_uploaded(self, data):
        message_id = data['message_id']
        content = {
            'command': 'file_uploaded',
            'message_id': message_id,
        }
        return self.send_chat_message(content)

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        return {
            'id': message.id,
            'user': message.user.get_full_name(),
            'user_id': message.user.id,
            'photo': f'{self.get_full_file_url(photo.url)}' if (photo := message.user.photo) else None,
            'content': message.text,
            'files': list(
                map(self.get_full_file_url,
                    map(lambda url: f'{settings.MEDIA_URL}{url}', message.files.values_list('file', flat=True)))
            ),
            'date_created': str(message.date_created)
        }

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message,
        'typing_message': typing_message,
        'delete_message': delete_message,
        'stop_typing_message': stop_typing_message,
        'file_uploading': file_uploading,
        'file_uploaded': file_uploaded,
    }

    def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        user = self.scope['user']
        self.group_name = self.chat_id

        if user.is_anonymous or not Chat.objects.filter(id=self.chat_id, users=user).exists():
            self.close()

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()

        self.fetch_messages()

        ChatPermission.objects.filter(chat_id=self.chat_id, user_id=user).update(is_online=True, unread_messages=0)

    def disconnect(self, close_code):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        user = self.scope['user']
        self.group_name = self.chat_id
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        ChatPermission.objects.filter(chat_id=self.chat_id, user_id=user).update(is_online=False)

    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['command']](self, data)

    def send_chat_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))


class NotificationConsumer(WebsocketConsumer):

    def fetch_notifications(self):
        notifications = Notification.objects.filter(Q(users=self.scope['user']))
        if self.scope['path'] == '/ws/notification/':
            notification = notifications.filter(~Q(section=Notification.CHATS))
            command = 'notifications'
            type = ''
        else:
            notification = notifications.filter(Q(section=Notification.CHATS))
            command = 'chat_notifications'
            type = 'chat_'

        content = {
            'command': command,
            f'{type}notifications': self.notifications_to_json(notification)

        }
        self.send_message(content)

    def view_notification(self, data):
        user = self.scope['user']
        notification = Notification.objects.filter(id=data['id']).first()
        if notification:
            if notification.section == Notification.CHATS:
                notification.delete()
            else:
                notification_seen = notification.users_seen.filter(user=user).first()
                notification_seen.is_viewed = True
                notification_seen.save()

    def notifications_to_json(self, notifications):
        result = []
        for notification in notifications:
            result.append(self.notification_to_json(notification))
        return result

    def notification_to_json(self, notification):
        user = self.scope['user']
        notification_seen = notification.users_seen.filter(user=user).first()
        return {
            'id': notification.id,
            'section': Notification.get_section_choices_label_value(notification.section),
            'text': notification.text,
            'is_viewed': notification_seen.is_viewed,
            'date_created': str(notification.date_created),
            'object_id': f'{notification.object_id if notification.object_id else ""}',
            'action_path': Notification.get_action_choices_label_value(notification.action_path),
        }

    commands = {
        'fetch_notifications': fetch_notifications,
        'view_notification': view_notification,
    }

    def connect(self):
        user = self.scope['user']

        if user.is_anonymous:
            self.close()
        else:
            condition = self.scope['path'] == '/ws/notification/'
            self.group_name = f'{user.id}{"" if condition else "_chat"}'
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            self.accept()

            self.fetch_notifications()

    def disconnect(self, close_code):
        self.close()

    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['command']](self, data)

    def notify(self, event):
        self.send(text_data=json.dumps(event['data']))

    def send_message(self, message):
        self.send(text_data=json.dumps(message))
