from rest_framework.routers import DefaultRouter
from django.urls import path

from app.websockets.views import (ChatViewSet,
                                  MessageViewSet,
                                  MessageFileViewSet,
                                  TicketViewSet, TicketView, IndexView, )

app_name = 'websockets'

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'message', MessageViewSet, basename='message')
router.register(r'file', MessageFileViewSet, basename='message-file')
router.register(r'ticket', TicketViewSet, basename='support-chat')

urlpatterns = router.urls


urlpatterns += [
    path('support-chat/<int:chat_id>/', TicketView.as_view(), name='support_chat'),
    path('js/', IndexView.as_view(), name='js'),
]
