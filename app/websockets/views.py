from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from app.websockets.models import Chat, Message, MessageFile, Ticket
from app.websockets.serializers import ChatBaseSerializer, MessageBaseSerializer, MessageFileBaseSerializer, \
    TicketBaseSerializer, TicketPermissionSerializer

from rest_framework.response import Response
from rest_framework import status

from app.core.util.get_jwt_token import get_jwt_token


class ChatViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatBaseSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(users=user)


class MessageViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageBaseSerializer
    permission_classes = (IsAuthenticated,)


class MessageFileViewSet(mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    queryset = MessageFile.objects.all()
    serializer_class = MessageFileBaseSerializer
    permission_classes = (IsAuthenticated,)


class TicketViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet, ):
    queryset = Ticket.objects.all()
    serializer_class = TicketBaseSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return self.serializer_class
        else:
            return TicketPermissionSerializer

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(chat__users=user).distinct()

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        chat = Chat.objects.create()
        chat.users.add(user)
        data['chat'] = chat.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@method_decorator(login_required, name='dispatch')
class TicketView(TemplateView):
    template_name = "websockets/index.html"
    model = Ticket


    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        chat_id = self.kwargs['chat_id']
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "chat_id":  chat_id,
                "token": get_jwt_token(user),
            }
        )
        return ctx


class IndexView(TemplateView):
    template_name = "websockets/index.js"
    content_type = "application/javascript"
