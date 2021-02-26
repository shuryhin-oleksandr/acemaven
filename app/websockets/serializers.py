from rest_framework import serializers

from app.websockets.models import Chat, Message, MessageFile, Ticket, ChatPermission


class ChatBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = (
            'id',
            'operation',
            'users',
            'ticket'
        )


class MessageBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            'id',
            'text',
            'user',
            'chat',
        )


class MessageFileBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageFile
        fields = (
            'id',
            'file',
            'message',
        )


class TicketBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            'id',
            'category',
            'topic',
            'description',
            'status',
            'chat',
            'aceid',
        )


class TicketPermissionSerializer(TicketBaseSerializer):
    unread_messages = serializers.SerializerMethodField()
    chat = serializers.SerializerMethodField()

    class Meta(TicketBaseSerializer.Meta):
        model = Ticket
        fields = TicketBaseSerializer.Meta.fields + ('unread_messages',)

    def get_unread_messages(self, obj):
        qs = ChatPermission.objects.filter(chat_id=obj.chat_id, user_id=self.context['request'].user.id).first()
        return qs.unread_messages

    def get_chat(self, obj):

        data = dict()

        if context := self.context:
            user = context['request'].user
            chat = obj.chat if hasattr(obj, 'chat') else None
            if chat:
                user_chat_permissions = user.chat_permissions.filter(chat=chat).first()
                data['chat'] = chat.id
                data['has_perm_to_read'] = user_chat_permissions.has_perm_to_read if user_chat_permissions else False
                data['has_perm_to_write'] = user_chat_permissions.has_perm_to_write if user_chat_permissions else False
        return data
