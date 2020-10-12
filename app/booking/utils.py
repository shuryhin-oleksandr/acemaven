from django.conf import settings
from django.db.models import Q

from app.booking.models import Surcharge


COUNTRY_CODE = settings.COUNTRY_OF_ORIGIN_CODE


def date_format(date):
    return '-'.join(date.split('/')[::-1])


def rate_surcharges_filter(rate, company):
    freight_rate = rate.freight_rate
    direction = 'export' if freight_rate.origin.code.startswith(COUNTRY_CODE) else 'import'
    location = freight_rate.origin if direction == 'export' else freight_rate.destination
    filter_fields = {
        'carrier': freight_rate.carrier,
        'direction': direction,
        'location': location,
        'shipping_mode': freight_rate.shipping_mode,
    }
    start_date_fields = {
        'start_date__gte': rate.start_date,
        'start_date__lte': rate.expiration_date,
    }
    end_date_fields = {
        'expiration_date__gte': rate.start_date,
        'expiration_date__lte': rate.expiration_date,
    }
    surcharges = Surcharge.objects.filter(
        Q(**filter_fields),
        Q(Q(**start_date_fields), Q(**end_date_fields), _connector='OR'),
        company=company,
    )
    return surcharges
