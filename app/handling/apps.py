from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class HandlingConfig(AppConfig):
    name = 'app.handling'
    verbose_name = _("Handling")
