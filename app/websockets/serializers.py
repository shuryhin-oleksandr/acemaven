from rest_framework import serializers

from app.websockets.models import Chat, Message, MessageFile


class ChatBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = (
            'id',
            'operation',
            'users',
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
