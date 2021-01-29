from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render

from app.websockets.models import Chat, Message, MessageFile
from app.websockets.serializers import ChatBaseSerializer, MessageBaseSerializer, MessageFileBaseSerializer


def notification(request):
    return render(request, 'websockets/notification.html')


def room(request, room_name):
    return render(request, 'websockets/room.html', {
        'room_name': room_name
    })


class ChatViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatBaseSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(users=user)


class MessageViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageBaseSerializer
    permission_classes = (IsAuthenticated, )


class MessageFileViewSet(mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    queryset = MessageFile.objects.all()
    serializer_class = MessageFileBaseSerializer
    permission_classes = (IsAuthenticated, )
