from rest_framework.routers import DefaultRouter

from app.websockets.views import (ChatViewSet,
                                  MessageViewSet,
                                  MessageFileViewSet,)


app_name = 'websockets'

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'message', MessageViewSet, basename='message')
router.register(r'file', MessageFileViewSet, basename='message-file')

urlpatterns = router.urls
