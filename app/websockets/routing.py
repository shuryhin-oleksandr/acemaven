from django.urls import re_path, path

from app.websockets.consumers import ChatConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/operation-chat/(?P<chat_id>\w+)/$', ChatConsumer.as_asgi()),
    path(r'ws/notification/', NotificationConsumer.as_asgi()),
    path(r'ws/chat_notification/', NotificationConsumer.as_asgi()),
]
