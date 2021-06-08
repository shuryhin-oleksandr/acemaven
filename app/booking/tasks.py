import datetime
import logging
from decimal import Decimal

import requests
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from app.core.models import Company
from config import settings
from config.celery import celery_app
from django.db.models import Q, Case, When, Value, CharField
from django.db.utils import ProgrammingError
from django.utils import timezone

from app.booking.models import Quote, Booking, Track, CancellationReason, Surcharge, FreightRate, ShipmentDetails, \
    Transaction
from app.booking.utils import sea_event_codes
from app.handling.models import ClientPlatformSetting, AirTrackingSetting, SeaTrackingSetting, GeneralSetting
from app.location.models import Country
from app.websockets.tasks import create_and_assign_notification, send_email
from app.websockets.models import Notification
from app.core.util.payment import review_payment, change_amount
from django.utils.translation import ugettext as _

logger = logging.getLogger("acemaven.task.logging")

try:
    MAIN_COUNTRY_CODE = Country.objects.filter(is_main=True).first().code
except (ProgrammingError, AttributeError):
    MAIN_COUNTRY_CODE = 'BR'


@celery_app.task(name='check_payment')
def check_payment(txid, base_url, developer_key, booking_id, token_uri, client_id, client_secret, basic_token, ):
    response, status_code = review_payment(base_url, developer_key, txid, token_uri, client_id, client_secret,
                                           basic_token)
    Transaction.objects.filter(txid=txid).update(response=response)

    if isinstance(response, dict):
        booking = Booking.objects.filter(id=booking_id).first()
        if status_code == 200:
            if 'pix' in response.keys() and response['status'] == 'CONCLUIDA':
                check_charge = Decimal(response['pix'][0]['valor']) == Transaction.objects.filter(
                    booking=booking_id).values_list('charge', flat=True).first()
                if check_charge:
                    booking.is_paid = True
                    booking.status = Booking.REQUEST_RECEIVED
                    booking.save()
                    booking.transactions.filter(status=Transaction.OPENED).update(status=Transaction.FINISHED)

                    client_contact_person_id = booking.client_contact_person_id
                    client_contact_person_email = booking.client_contact_person.email

                    text_body = 'Payment on booking number {aceid} is success'
                    text_params = {'aceid':booking.aceid}
                    create_and_assign_notification.delay(
                        Notification.REQUESTS,
                        text_body,
                        text_params,
                        [client_contact_person_id, ],
                        Notification.OPERATION,
                        booking_id,
                    )
                    send_email.delay(text_body, text_params, [client_contact_person_id, ],
                                     object_id=f'{settings.DOMAIN_ADDRESS}operations/{booking.id}')

                    agent_text_body = 'A new booking request {aceid} has been received.'
                    agent_text_params = {'aceid':booking.aceid}
                    ff_company = booking.freight_rate.company
                    users_ids = list(
                        ff_company.users.filter(role__groups__name__in=('master', 'agent')).values_list('id', flat=True)
                    )
                    create_and_assign_notification.delay(
                        Notification.REQUESTS,
                        agent_text_body,
                        agent_text_params,
                        users_ids,
                        Notification.BOOKING,
                        object_id=booking.id,
                    )

                    send_email.delay(agent_text_body, agent_text_params, users_ids,
                                     object_id=f'{settings.DOMAIN_ADDRESS}requests/booking/{booking.id}')

                    client_text_body = 'The booking request {aceid} has been sent to "{name}".'
                    client_text_params = {'aceid':booking.aceid, 'name':ff_company.name}
                    create_and_assign_notification.delay(
                        Notification.REQUESTS,
                        client_text_body,
                        client_text_params,
                        [client_contact_person_id, ],
                        Notification.OPERATION,
                        object_id=booking.id,
                    )
                    send_email.delay(client_text_body, client_text_params, [client_contact_person_id, ],
                                     object_id=f'{settings.DOMAIN_ADDRESS}operations/{booking.id}')
                    print("Payment success")

                else:
                    print("Charge not match")
                    check_payment.apply_async((txid, base_url, developer_key, booking_id, token_uri,
                                               client_id, client_secret, basic_token,),
                                              eta=now() + datetime.timedelta(seconds=7200),
                                              expires=259200)
            else:
                print("No pix/status in response")
                check_payment.apply_async((txid, base_url, developer_key, booking_id, token_uri,
                                           client_id, client_secret, basic_token,),
                                          eta=now() + datetime.timedelta(days=1),
                                          expires=259200)
        else:
            user_id = booking.client_contact_person_id
            text_body = 'Have some problems with payment on booking number {aceid}, please, contact support team.'
            text_params = {'aceid':booking.aceid}

            create_and_assign_notification.delay(
                Notification.REQUESTS,
                text_body,
                text_params,
                [user_id, ],
                Notification.BILLING,
                booking_id,
            )
            send_email.delay(text_body, text_params, [user_id, ], object_id=f'{settings.DOMAIN_ADDRESS}billing_pending/')


@celery_app.task(name='test')
def test():
    print('test')
    test.apply_async(eta=now() + datetime.timedelta(days=1),
                     expires=259200)


@celery_app.task(name='change_charge')
def change_charge(base_url, new_amount, developer_key, txid, is_prod, booking_id, token_uri, client_id, client_secret,
                  basic_token):
    response, status_code = change_amount(base_url, new_amount, developer_key, txid, is_prod, token_uri, client_id,
                                          client_secret, basic_token)
    Transaction.objects.filter(txid=txid).update(response=response)

    booking = Booking.objects.filter(id=booking_id).first()
    client_contact_person_id = booking.client_contact_person_id
    client_contact_person_email = booking.client_contact_person.email

    if isinstance(response, dict):
        if status_code == 201:
            text_body = 'Update charge on booking number {aceid} is success'
            text_params = {'aceid':booking.aceid}
            create_and_assign_notification.delay(
                Notification.OPERATIONS,
                text_body,
                text_params,
                [client_contact_person_id, ],
                Notification.OPERATION,
                booking_id,
            )
            send_email.delay(text_body, text_params, [client_contact_person_id, ],
                             object_id=f'{settings.DOMAIN_ADDRESS}operations/{booking.id}')
        else:
            text_body = 'Have some problems with updating charge on booking number {aceid}, please, contact support team.'
            text_params = {'aceid':booking.aceid}
            message_body = _(
                'Have some problems with updating charge on booking number {aceid}, please, contact support team.') \
                .format(aceid=booking.aceid)
            create_and_assign_notification.delay(
                Notification.OPERATIONS,
                text_body,
                text_params,
                [client_contact_person_id, ],
                Notification.BILLING,
                booking_id,
            )
            send_email.delay(text_body, text_params, [client_contact_person_id, ],
                       object_id=f'{settings.DOMAIN_ADDRESS}billing_pending/')
            raise ValueError


@celery_app.task(name='archive_quotes')
def daily_archive_expired_quotes():
    settings_days_limit = ClientPlatformSetting.load().number_of_days
    now_date = timezone.localtime().date()
    Quote.objects.filter(
        Q(
            date_created__lt=now_date - datetime.timedelta(days=settings_days_limit),
            date_to__lt=now_date - datetime.timedelta(days=14),
            _connector=Q.OR,
        ),
        is_archived=False,
    ).update(is_archived=True)


@celery_app.task(name='discard_unpaid_bookings')
def daily_discard_unpaid_client_bookings():
    settings_days_limit = GeneralSetting.load().number_of_days_request_can_stay
    now_date = timezone.localtime().date()
    Booking.objects.filter(
        status=Booking.PENDING,
        date_created__lt=now_date - datetime.timedelta(days=settings_days_limit),
        is_paid=False,
    ).update(status=Booking.DISCARDED)


@celery_app.task(name='cancel_unconfirmed_bookings')
def daily_cancel_unconfirmed_agent_bookings():
    settings = GeneralSetting.load()
    now_date = timezone.localtime().date()
    queryset = Booking.objects.filter(
        status=Booking.ACCEPTED,
    ).annotate(
        direction=Case(When(freight_rate__origin__code__startswith=MAIN_COUNTRY_CODE, then=Value('export')),
                       default=Value('import'),
                       output_field=CharField(),
                       )
    ).filter(Q(
        Q(
            direction='export',
            date_accepted_by_agent__lt=now_date - datetime.timedelta(days=settings.export_deadline_days),
        ),
        Q(
            direction='import',
            date_accepted_by_agent__lt=now_date - datetime.timedelta(days=settings.import_deadline_days),
        ),
        _connector=Q.OR,
    ))
    queryset.update(status=Booking.CANCELED_BY_SYSTEM)
    for operation in queryset:
        CancellationReason.objects.create(
            reason=CancellationReason.OTHER,
            comment=_('Operation cancelled according to expired time for confirming booking by an agent'),
            booking=operation,
        )


@celery_app.task(name='post_awb_number')
def send_awb_number_to_air_tracking_api(booking_number, booking_id, agent_contact_person_id):
    logger.info(_(f'Sending new airway bill number to track [{booking_number}]'))
    settings = AirTrackingSetting.load()
    url = settings.url
    headers = {
        'Password': settings.password,
        'User': settings.user,
    }
    data = {
        "waybillIdentification": [booking_number],
        "notifyAddressType": "PIMA",
        "notifyAddress": settings.pima,
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        confirmation = response.json().get('confirmations')[0]
        if (error := confirmation.get('error')) == 'Wrong format of waybill number':
            message_body = _('The shipment {booking_number} cannot be tracked because of wrong booking number.') \
                .format(booking_number=booking_number)
            create_and_assign_notification.delay(
                Notification.OPERATIONS,
                'The shipment {booking_number} cannot be tracked because of wrong booking number.',
                {'booking_number':booking_number},
                [agent_contact_person_id, ],
                Notification.OPERATION,
                object_id=booking_id,
            )

        else:
            pass
            # Add notification to acemaven platform
    else:
        pass
        # Add notification to acemaven platform

    logger.info(_(f'Response text for airway bill number [{booking_number}] - {response.text}'))


@celery_app.task(name='track_sea_operations')
def track_confirmed_sea_operations():
    logger.info(_(f'Starting to get track statuses for confirmed operations'))
    settings = SeaTrackingSetting.load()
    url = settings.url
    api_key = settings.api_key
    operations = Booking.objects.filter(
        status=Booking.CONFIRMED,
        freight_rate__shipping_mode__shipping_type__title='sea',
        automatic_tracking=True,
        vessel_arrived=False,
        original_booking__isnull=True,
    )
    for operation in operations:
        direction = 'export' if operation.freight_rate.origin.code.startswith(MAIN_COUNTRY_CODE) else 'import'
        booking_number = operation.shipment_details.first().booking_number
        scac = operation.freight_rate.carrier.scac
        base_url = f'?type=BK&number={booking_number}&sealine={scac}&api_key={api_key}'
        data_url = f'{url}reference{base_url}'
        route_url = f'{url}route{base_url}'

        data_response = requests.get(data_url)
        data_json = data_response.json() if (data_status_code := data_response.status_code) == 200 \
            else {
            'status': 'error',
            'message': f'Status code - {data_status_code}',
        }

        if data_json.get('status') == 'error':
            if (message := data_json.get('message')) == 'WRONG_NUMBER':
                text_body = 'The shipment {aceid} cannot be tracked because of wrong booking number.'
                text_params = {'aceid':operation.aceid}

                create_and_assign_notification.delay(
                    Notification.OPERATIONS,
                    text_body,
                    text_params,
                    [operation.agent_contact_person_id, ],
                    Notification.OPERATION,
                    object_id=operation.id,
                )
                send_email.delay(text_body, text_params, [operation.agent_contact_person_id, ],
                                 object_id=f'{settings.DOMAIN_ADDRESS}operations/{operation.id}')


            else:
                pass
                # Add notification to acemaven platform
            break

        shipment_details = operation.shipment_details.first()

        if 'containers' in data_json['data']:
            for container in data_json['data']['containers']:
                for event in container['events']:
                    status = event.get('status', 'UNK')
                    event['status'] = sea_event_codes.get(status)
                    if status == 'VAD':
                        operation.vessel_arrived = True
                        operation.save()
                    if status == 'VDL' and not shipment_details.actual_date_of_departure:
                        shipment_details.actual_date_of_departure = timezone.localtime()
                        shipment_details.save()
                        if direction == 'import':
                            text_body = 'The shipment {aceid} has departed from {origin}.'
                            text_params = {'aceid':operation.aceid, 'origin':operation.freight_rate.origin.code}

                            create_and_assign_notification.delay(
                                Notification.OPERATIONS_IMPORT,
                                text_body,
                                text_params,
                                [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                                Notification.OPERATION,
                                object_id=operation.id,
                            )
                            send_email.delay(text_body, text_params, [operation.agent_contact_person_id,
                                                                      operation.client_contact_person_id, ],
                                             object_id=f'{settings.DOMAIN_ADDRESS}operations/{operation.id}')

                    event['location'] = next(
                        filter(lambda x: x.get('id') == event['location'], data_json['data'].get('locations')), {}
                    ).get('name', '')
                    event['vessel'] = next(
                        filter(lambda x: x.get('id') == event['vessel'], data_json['data'].get('vessels')), {}
                    ).get('name', '')

        if 'route' in data_json['data']:
            date = data_json['data']['route'].get('postpod', {}).get('date')
            if date and not shipment_details.actual_date_of_arrival:
                shipment_details.actual_date_of_arrival = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                shipment_details.save()
                if direction == 'export':
                    text_body = 'The shipment {aceid} has arrived at {destination}.'
                    text_params = {'aceid':operation.aceid, 'destination':operation.freight_rate.destination.code}

                    create_and_assign_notification.delay(
                        Notification.OPERATIONS_EXPORT,
                        text_body,
                        text_params,
                        [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                        Notification.OPERATION,
                        object_id=operation.id,
                    )
                    send_email.delay(text_body,text_params
                                     [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                                     object_id=f'{settings.DOMAIN_ADDRESS}operations/{operation.id}')

        route_response = requests.get(route_url)
        route_json = route_response.json() if (route_status_code := route_response.status_code) == 200 \
            else {
            'status': 'error',
            'message': f'Status code - {route_status_code}',
        }

        track, _ = Track.objects.get_or_create(
            manual=False,
            booking=operation,
            defaults={'booking': operation}
        )
        track.data = data_json
        track.route = route_json
        track.save()


@celery_app.task(name='notify_users_of_expiring_surcharges')
def daily_notify_users_of_expiring_surcharges():
    now_date = timezone.localtime().date()
    surcharges = Surcharge.objects.filter(
        temporary=False,
        is_archived=False,
        expiration_date=now_date + datetime.timedelta(days=5),
    )
    for surcharge in surcharges:
        users_ids = list(surcharge.company.role_set.filter(
            groups__name__in=('master', 'agent')
        ).values_list('user__id', flat=True))
        message_body = _(
            'Surcharges are about to expire. Please, extend its expiration rate or create a new one with the updated costs.')
        create_and_assign_notification.delay(
            Notification.SURCHARGES,
            message_body,
            {},
            users_ids,
            Notification.SURCHARGE,
            object_id=surcharge.id,
        )
        send_email.delay(message_body, {}, users_ids,
                         object_id=f'{settings.DOMAIN_ADDRESS}services/surcharge/{surcharge.id}')

    for user in get_user_model().objects.filter(role__groups__name__in=('master', 'agent'),
                                                emailnotificationsetting__surcharge_expiration=True,
                                                companies__type=Company.FREIGHT_FORWARDER,
                                                ).distinct():
        expiration_days = user.emailnotificationsetting.surcharge_expiration_days
        for surcharge in user.get_company().surcharges.filter(temporary=False,
                                                              is_archived=False,
                                                              expiration_date=now_date + datetime.timedelta(
                                                                  days=expiration_days
                                                              ), ):
            message_body = _(
                'Surcharges are about to expire. Please, extend its expiration rate or create a new one with the updated costs.')

            send_email(
                message_body, {},
                [user.id,],
                object_id=f'{settings.DOMAIN_ADDRESS}services/surcharge/{surcharge.id}')


@celery_app.task(name='notify_users_of_expiring_freight_rates')
def daily_notify_users_of_expiring_freight_rates():
    now_date = timezone.localtime().date()
    freight_rates = FreightRate.objects.filter(
        is_active=True,
        temporary=False,
        is_archived=False,
        rates__expiration_date=now_date + datetime.timedelta(days=5),
    ).distinct()
    for freight_rate in freight_rates:
        users_ids = list(freight_rate.company.role_set.filter(
            groups__name__in=('master', 'agent')
        ).values_list('user__id', flat=True))
        message_body = _(
            'Rates are about to expire.Please, extend its expiration rate or create a new one with the updated costs.')
        create_and_assign_notification.delay(
            Notification.FREIGHT_RATES,
            message_body,
            {},
            users_ids,
            Notification.FREIGHT_RATE,
            object_id=freight_rate.id,
        )

        send_email.delay(message_body, {}, users_ids,
                         object_id=f'{settings.DOMAIN_ADDRESS}services/rate/{freight_rate.id}')

    for user in get_user_model().objects.filter(role__groups__name__in=('master', 'agent'),
                                                emailnotificationsetting__freight_rate_expiration=True,
                                                companies__type=Company.FREIGHT_FORWARDER,
                                                ).distinct():
        expiration_days = user.emailnotificationsetting.freight_rate_expiration_days
        for freight_rate in user.get_company().freight_rates.filter(is_active=True,
                                                                    temporary=False,
                                                                    is_archived=False,
                                                                    rates__expiration_date=now_date + datetime.timedelta(
                                                                        days=expiration_days), ).distinct():
            message_body = _(
                'Rates are about to expire.Please, extend its expiration rate or create a new one with the updated costs.')

            send_email(message_body, {}
                       [user.id, ],
                       object_id=f'{settings.DOMAIN_ADDRESS}services/rate/{freight_rate.id}')


@celery_app.task(name='notify_users_of_import_sea_shipment_arrival')
def daily_notify_users_of_import_sea_shipment_arrival():
    now_date = timezone.localtime().date()
    import_shipment_details = ShipmentDetails.objects.annotate(
        direction=Case(When(booking__freight_rate__origin__code__startswith=MAIN_COUNTRY_CODE, then=Value('export')),
                       default=Value('import'),
                       output_field=CharField(),
                       )
    ).filter(
        direction='import',
        booking__freight_rate__shipping_mode__shipping_type__title='sea',
    )
    notification_shipment_details = import_shipment_details.filter(
        date_of_arrival__date=now_date + datetime.timedelta(days=3),
    )
    for shipment_detail in notification_shipment_details:
        booking = shipment_detail.booking
        message_body = _(
            'The shipment {aceid} is set to arrive in 3 days at {destination}.')\
            .format(aceid=booking.aceid, destination=booking.freight_rate.destination.code)
        create_and_assign_notification.delay(
            Notification.OPERATIONS_IMPORT,
            'The shipment {aceid} is set to arrive in 3 days at {destination}.',
            {'aceid':booking.aceid, 'destination':booking.freight_rate.destination.code},
            [booking.agent_contact_person_id, booking.client_contact_person_id, ],
            Notification.OPERATION,
            object_id=booking.id,
        )
    for user in get_user_model().objects.filter(
            role__groups__name__in=('master', 'agent', 'client'),
            emailnotificationsetting__sea_import_shipment_arrival_alert=True, ).distinct():
        expiration_days = user.emailnotificationsetting.sea_import_shipment_arrival_alert_days
        filter_data = dict()
        if user.get_company().type == Company.FREIGHT_FORWARDER:
            filter_data['booking__agent_contact_person'] = user
        else:
            filter_data['booking__client_contact_person'] = user
        email_shipment_details = import_shipment_details.filter(
            date_of_arrival__date=now_date + datetime.timedelta(days=expiration_days),
            **filter_data,
        )

        for shipment_detail in email_shipment_details:
            booking = shipment_detail.booking
            text_body = 'The shipment {aceid} is set to arrive in 3 days at {destination}.'
            text_params = {'aceid': booking.aceid, 'destination': booking.freight_rate.destination}

            send_email(text_body, text_params, [user.id, ],
                       object_id=f'{settings.DOMAIN_ADDRESS}operations/{booking.id}')
