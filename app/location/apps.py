from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class LocationConfig(AppConfig):
    name = 'app.location'
    verbose_name = _("Location")
