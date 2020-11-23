from decimal import Decimal

from django.db.models import Q

from app.booking.models import Surcharge, Charge, FreightRate
from app.handling.models import GlobalFee, ShippingMode, ExchangeRate, ContainerType, PackagingType, Port
from app.location.models import Country


main_country = Country.objects.filter(is_main=True).first()
MAIN_COUNTRY_CODE = main_country.code if main_country else 'BR'


def date_format(date):
    return '-'.join(date.split('/')[::-1])


def rate_surcharges_filter(rate, company, temporary=False):
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
    if not temporary:
        surcharges = surcharges.filter(temporary=temporary)
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
            subtotal = float(subtotal)
            cost_per_pack = float(cost_per_pack)
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
        usage_fee_data['cost'] = float(usage_fee.charge)
        subtotal = usage_fee.charge * Decimal(cargo_group.get('volume'))
        subtotal = float(subtotal)
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
                           main_currency_code,
                           exchange_rate,
                           booking_fee=None,
                           volume=1,
                           total_weight_per_pack=1,
                           total_weight=1,):
    freight = dict()
    code = rate.currency.code
    freight['currency'] = code
    freight['cost'] = float(total_weight_per_pack * rate.rate)
    subtotal = volume * total_weight * rate.rate
    if booking_fee:
        subtotal, booking_fee_value_in_local_curr = calculate_fee(booking_fee,
                                                                  rate,
                                                                  main_currency_code,
                                                                  exchange_rate,
                                                                  subtotal)
        booking_fee_value_in_local_curr = float(booking_fee_value_in_local_curr)
        freight['booking_fee'] = booking_fee_value_in_local_curr
        add_currency_value(totals, 'booking_fee', booking_fee_value_in_local_curr)
    subtotal = float(subtotal)
    freight['subtotal'] = subtotal
    add_currency_value(totals, code, subtotal)
    add_currency_value(totals['total_freight_rate'], code, subtotal)
    return freight


def calculate_freight_rate_charges(freight_rate,
                                   freight_rate_dict,
                                   cargo_groups,
                                   shipping_mode,
                                   main_currency_code,
                                   date_from,
                                   date_to,
                                   container_type_ids_list,
                                   booking_fee=None,
                                   service_fee=0):
    totals = dict()
    totals['total_freight_rate'] = dict()
    totals['total_surcharge'] = dict()
    result = dict()
    result['freight_rate'] = freight_rate_dict
    result['cargo_groups'] = []
    if shipping_mode.is_need_volume:
        rate = freight_rate.rates.first()
        exchange_rate = ExchangeRate.objects.filter(currency__code=rate.currency.code).first()
        for cargo_group in cargo_groups:
            new_cargo_group = dict()
            total_weight_per_pack, total_weight = wm_calculate(cargo_group, shipping_mode.shipping_type.title)

            new_cargo_group['freight'] = calculate_freight_rate(totals,
                                                                rate,
                                                                main_currency_code,
                                                                exchange_rate,
                                                                booking_fee=booking_fee,
                                                                total_weight_per_pack=total_weight_per_pack,
                                                                total_weight=total_weight)

            surcharge = rate.surcharges.filter(start_date__lte=date_from,
                                               expiration_date__gte=date_to).first()
            charges = surcharge.charges.all()
            usage_fee = surcharge.usage_fees.filter(container_type=cargo_group.get('container_type')).first()
            calculate_additional_surcharges(totals,
                                            charges,
                                            usage_fee,
                                            cargo_group,
                                            shipping_mode,
                                            new_cargo_group,
                                            total_weight_per_pack)
            new_cargo_group['volume'] = cargo_group.get('volume')
            container_type = cargo_group.get('container_type')
            packaging_type = cargo_group.get('packaging_type')
            new_cargo_group['cargo_type'] = ContainerType.objects.filter(id=container_type).first().code \
                if container_type else PackagingType.objects.filter(id=packaging_type).first().description

            result['cargo_groups'].append(new_cargo_group)
    else:
        rates = freight_rate.rates.all()
        for cargo_group in cargo_groups:
            new_cargo_group = dict()
            rate = rates.filter(container_type=cargo_group.get('container_type')).first()
            exchange_rate = ExchangeRate.objects.filter(currency__code=rate.currency.code).first()

            new_cargo_group['freight'] = calculate_freight_rate(totals,
                                                                rate,
                                                                main_currency_code,
                                                                exchange_rate,
                                                                booking_fee=booking_fee,
                                                                volume=cargo_group.get('volume'))

            surcharge = rate.surcharges.filter(start_date__lte=date_from,
                                               expiration_date__gte=date_to).first()
            charges = surcharge.charges.all()
            usage_fee = surcharge.usage_fees.filter(container_type=cargo_group.get('container_type')).first()
            calculate_additional_surcharges(totals,
                                            charges,
                                            usage_fee,
                                            cargo_group,
                                            shipping_mode,
                                            new_cargo_group)
            new_cargo_group['volume'] = cargo_group.get('volume')
            container_type = cargo_group.get('container_type')
            new_cargo_group['cargo_type'] = ContainerType.objects.filter(id=container_type).first().code

            result['cargo_groups'].append(new_cargo_group)

    doc_fee = dict()
    filter_data = {}
    if shipping_mode.has_freight_containers:
        filter_data['container_type__id'] = container_type_ids_list[0]
    surcharge = freight_rate.rates.filter(**filter_data).first().surcharges.filter(
        start_date__lte=date_from,
        expiration_date__gte=date_to,
    ).first()
    charge = surcharge.charges.filter(additional_surcharge__is_document=True).first()
    doc_fee_charge = float(charge.charge)
    doc_fee['currency'] = charge.currency.code
    doc_fee['cost'] = doc_fee_charge
    doc_fee['subtotal'] = doc_fee_charge
    result['doc_fee'] = doc_fee
    add_currency_value(totals, charge.currency.code, doc_fee_charge)

    if service_fee:
        service_fee_dict = dict()
        service_fee_dict['currency'] = main_currency_code
        service_fee_dict['cost'] = service_fee
        service_fee_dict['subtotal'] = service_fee
        result['service_fee'] = service_fee_dict
        add_currency_value(totals, main_currency_code, service_fee)

    total_freight_rate = totals.pop('total_freight_rate')
    total_surcharge = totals.pop('total_surcharge')
    result['total_freight_rate'] = total_freight_rate
    result['total_surcharge'] = total_surcharge

    total_booking_fee = totals.pop('booking_fee', 0)
    pay_to_book = service_fee + total_booking_fee
    result['totals'] = totals
    if service_fee or booking_fee:
        result['pay_to_book'] = {
            'service_fee': service_fee,
            'booking_fee': total_booking_fee,
            'pay_to_book': pay_to_book,
            'currency': main_currency_code,
        }

    return result


def get_fees(company, shipping_mode):
    local_fees = company.fees.filter(shipping_mode=shipping_mode)
    global_fees = GlobalFee.objects.filter(shipping_mode=shipping_mode)
    local_booking_fee = local_fees.filter(fee_type=GlobalFee.BOOKING, is_active=True).first()
    local_service_fee = local_fees.filter(fee_type=GlobalFee.SERVICE, is_active=True).first()
    booking_fee = local_booking_fee if local_booking_fee else \
        global_fees.filter(fee_type=GlobalFee.BOOKING, is_active=True).first()
    service_fee = local_service_fee if local_service_fee else \
        global_fees.filter(fee_type=GlobalFee.SERVICE, is_active=True).first()
    service_fee = service_fee.value if service_fee else 0

    return booking_fee, service_fee


def get_data_info(data):
    cargo_groups = data.pop('cargo_groups')
    container_type_ids_list = [group.get('container_type') for group in cargo_groups if 'container_type' in group]
    dangerous_list = list(filter(lambda x: x.get('dangerous'), cargo_groups))
    cold_list = list(filter(lambda x: x.get('frozen') == 'cold', cargo_groups))
    date_from = date_format(data.pop('date_from'))
    date_to = date_format(data.pop('date_to'))
    return cargo_groups, container_type_ids_list, dangerous_list, cold_list, date_from, date_to


def surcharge_search(data, company):
    shipping_mode = ShippingMode.objects.filter(id=data.get('shipping_mode')).first()
    cargo_groups, container_type_ids_list, dangerous_list, cold_list, date_from, date_to = get_data_info(data)
    port = Port.objects.get(id=data['origin'])
    direction = 'export' if port.code.startswith(MAIN_COUNTRY_CODE) else 'import'
    location = data['origin'] if direction == 'export' else data['destination']
    filter_fields = {
        'carrier': data['carrier'],
        'direction': direction,
        'location': location,
        'shipping_mode': shipping_mode,
        'company': company,
        'temporary': False,
        'start_date__lte': date_from,
        'expiration_date__gte': date_to,
    }

    queryset = Surcharge.objects.filter(**filter_fields)

    if shipping_mode.has_surcharge_containers:
        for container_type_id in container_type_ids_list:
            queryset = queryset.filter(
                usage_fees__charge__isnull=False,
                usage_fees__container_type__id=container_type_id
            )
    if dangerous_list:
        queryset = queryset.filter(
            charges__additional_surcharge__is_dangerous=True,
            charges__charge__isnull=False
        )
    if cold_list:
        queryset = queryset.filter(
            charges__additional_surcharge__is_cold=True,
            charges__charge__isnull=False
        )

    return queryset


def freight_rate_search(data, company=None):
    shipping_mode = ShippingMode.objects.filter(id=data.get('shipping_mode')).first()
    cargo_groups, container_type_ids_list, dangerous_list, cold_list, date_from, date_to = get_data_info(data)

    data['rates__start_date__lte'] = date_from
    data['rates__expiration_date__gte'] = date_to
    data['rates__surcharges__start_date__lte'] = date_from
    data['rates__surcharges__expiration_date__gte'] = date_to

    freight_rates = FreightRate.objects.filter(**data, is_active=True, temporary=False)

    if shipping_mode.has_freight_containers:
        for container_type_id in container_type_ids_list:
            freight_rates = freight_rates.filter(
                rates__rate__isnull=False,
                rates__container_type__id=container_type_id
            )
    if shipping_mode.has_surcharge_containers:
        for container_type_id in container_type_ids_list:
            freight_rates = freight_rates.filter(
                rates__surcharges__usage_fees__charge__isnull=False,
                rates__surcharges__usage_fees__container_type__id=container_type_id
            )

    if dangerous_list:
        freight_rates = freight_rates.filter(
            rates__surcharges__charges__additional_surcharge__is_dangerous=True,
            rates__surcharges__charges__charge__isnull=False
        )
    if cold_list:
        freight_rates = freight_rates.filter(
            rates__surcharges__charges__additional_surcharge__is_cold=True,
            rates__surcharges__charges__charge__isnull=False
        )
    if company:
        freight_rates = freight_rates.filter(
            company=company,
        )

    return freight_rates, shipping_mode
