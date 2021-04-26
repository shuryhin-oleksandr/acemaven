from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ChatConfig(AppConfig):
    name = 'app.websockets'
    verbose_name = _("Websockets")

    def ready(self):
        import app.websockets.signals
