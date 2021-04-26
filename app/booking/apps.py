from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class BookingConfig(AppConfig):
    name = 'app.booking'
    verbose_name = _("Booking")
