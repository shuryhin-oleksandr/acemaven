from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = 'app.websockets'

    def ready(self):
        import app.websockets.signals
