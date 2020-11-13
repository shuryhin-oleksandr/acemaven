from decimal import Decimal

from django.db.models import Q

from app.booking.models import Surcharge, Charge
from app.handling.models import GlobalFee
from app.location.models import Country


main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


def date_format(date):
    return '-'.join(date.split('/')[::-1])


def rate_surcharges_filter(rate, company):
    freight_rate = rate.freight_rate
    direction = 'export' if freight_rate.origin.code.startswith(MAIN_COUNTRY_CODE) else 'import'
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


def wm_calculate(data, shipping_type=None):
    if not shipping_type:
        shipping_type = data.get('shipping_type')
    weight_measurement = data.get('weight_measurement')
    length_measurement = data.get('length_measurement')
    weight = Decimal(data.get('weight'))
    height = Decimal(data.get('height'))
    length = Decimal(data.get('length'))
    width = Decimal(data.get('width'))
    volume = data.get('volume')
    if shipping_type == 'air':
        gross_weight = weight if weight_measurement == 'kg' else weight * 1000
        divider = 6000 if length_measurement == 'cm' else 0.006
    else:
        gross_weight = weight if weight_measurement == 't' else weight / 1000
        divider = 1 if length_measurement == 'm' else 1000000
    total_volume = height * length * width / Decimal(divider)
    total_weight_per_pack = gross_weight if gross_weight > total_volume else total_volume
    total_weight = total_weight_per_pack * volume
    return round(total_weight_per_pack, 2), round(total_weight, 2)


def add_currency_value(totals, code, subtotal):
    totals[code] = totals[code] + subtotal if code in totals else subtotal


def calculate_additional_surcharges(totals,
                                    charges,
                                    usage_fee,
                                    cargo_group,
                                    shipping_mode,
                                    new_cargo_group,
                                    total_weight_per_pack=0):
    for charge in charges:
        data = dict()
        if not charge.additional_surcharge.is_document:
            if charge.additional_surcharge.is_dangerous and not cargo_group.get('dangerous'):
                continue
            elif charge.additional_surcharge.is_cold and not cargo_group.get('frozen'):
                continue
            fixed_cost = False
            cost_per_pack = charge.charge
            if shipping_mode.is_need_volume:
                if (condition := charge.conditions) == Charge.WM:
                    cost_per_pack = total_weight_per_pack * charge.charge
                elif condition == Charge.PER_WEIGHT:
                    cost_per_pack = Decimal(cargo_group.get('weight')) * charge.charge
                elif condition == Charge.FIXED:
                    fixed_cost = True
            subtotal = cost_per_pack * Decimal(cargo_group.get('volume')) if not fixed_cost else cost_per_pack
            code = charge.currency.code
            data['currency'] = code
            data['cost'] = cost_per_pack
            data['subtotal'] = subtotal
            new_cargo_group[charge.additional_surcharge.title.split()[0].lower()] = data
            add_currency_value(totals, code, subtotal)
            add_currency_value(totals['total_surcharge'], code, subtotal)

    if shipping_mode.has_surcharge_containers:
        usage_fee_data = dict()
        code = usage_fee.currency.code
        usage_fee_data['currency'] = code
        usage_fee_data['cost'] = usage_fee.charge
        subtotal = usage_fee.charge * Decimal(cargo_group.get('volume'))
        usage_fee_data['subtotal'] = subtotal
        data_key = 'usage_fee' if shipping_mode.is_need_volume else 'handling'
        new_cargo_group[data_key] = usage_fee_data
        add_currency_value(totals, code, subtotal)
        add_currency_value(totals['total_surcharge'], code, subtotal)


def calculate_fee(booking_fee, rate, main_currency_code, exchange_rate, subtotal):
    if booking_fee.fee_type == GlobalFee.FIXED:
        if rate.currency.code != main_currency_code:
            booking_fee_value_in_foreign_curr = booking_fee.value / (exchange_rate.rate * exchange_rate.spread)
        else:
            booking_fee_value_in_foreign_curr = booking_fee.value
        booking_fee_value_in_local_curr = booking_fee.value
    else:
        booking_fee_value_in_foreign_curr = subtotal * booking_fee.value
        if rate.currency.code != main_currency_code:
            booking_fee_value_in_local_curr = booking_fee_value_in_foreign_curr / (
                        exchange_rate.rate * exchange_rate.spread)
        else:
            booking_fee_value_in_local_curr = booking_fee_value_in_foreign_curr
    subtotal += booking_fee_value_in_foreign_curr
    return subtotal, booking_fee_value_in_local_curr


def calculate_freight_rate(totals,
                           rate,
                           booking_fee,
                           main_currency_code,
                           exchange_rate,
                           volume=1,
                           total_weight_per_pack=1,
                           total_weight=1):
    freight = dict()
    code = rate.currency.code
    freight['currency'] = code
    freight['cost'] = total_weight_per_pack * rate.rate
    subtotal = volume * total_weight * rate.rate
    booking_fee_value_in_local_curr = 0
    if booking_fee:
        subtotal, booking_fee_value_in_local_curr = calculate_fee(booking_fee,
                                                                  rate,
                                                                  main_currency_code,
                                                                  exchange_rate,
                                                                  subtotal)
    freight['subtotal'] = subtotal
    freight['booking_fee'] = booking_fee_value_in_local_curr
    add_currency_value(totals, 'booking_fee', booking_fee_value_in_local_curr)
    add_currency_value(totals, code, subtotal)
    add_currency_value(totals['total_freight_rate'], code, subtotal)
    return freight
