from rest_framework.routers import DefaultRouter

from django.urls import path

from app.websockets.views import (room,
                                  notification,
                                  ChatViewSet,
                                  MessageViewSet,
                                  MessageFileViewSet,)


app_name = 'websockets'

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'message', MessageViewSet, basename='message')
router.register(r'file', MessageFileViewSet, basename='message-file')

urlpatterns = router.urls

urlpatterns += [
    path('notification/', notification, name='notification'),
    path('chat/<str:room_name>/', room, name='room'),
]
