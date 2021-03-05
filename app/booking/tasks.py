import datetime
import logging
import requests
from django.contrib.auth import get_user_model

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
from app.core.util.payment import review_payment

logger = logging.getLogger("acemaven.task.logging")

try:
    MAIN_COUNTRY_CODE = Country.objects.filter(is_main=True).first().code
except (ProgrammingError, AttributeError):
    MAIN_COUNTRY_CODE = 'BR'


@celery_app.task(name='check_payment')
def check_payment(txid, base_url, developer_key, booking_id, token_uri, client_id, client_secret, basic_token,
                  users_ids):
    response, status_code = review_payment(base_url, developer_key, txid, token_uri, client_id, client_secret,
                                           basic_token)
    Transaction.objects.filter(txid=txid).update(response=response)

    if isinstance(response, dict):
        if status_code == 200:
            if 'pix' in response.keys() and response['status'] == 'CONCLUIDA':
                check_charge = response['pix'][0]['valor']['original'] == Transaction.objects.filter(
                    booking=booking_id).values_list('charge', flat=True).first()
                if check_charge:
                    Booking.objects.filter(id=booking_id).update(is_paid=True, status=Booking.REQUEST_RECEIVED)
                    message_body = f'Payment on booking number {booking_id} is success'
                    create_and_assign_notification(
                        Notification.REQUESTS,
                        message_body,
                        users_ids, #TODO users ids
                        Notification.BILLING,
                        booking_id,
                    )
                else:
                    check_payment.apply_async(countdown=7200, expires=259200)
            else:
                check_payment.apply_async(countdown=7200, expires=259200)
        else:
            message_body = f'Have some problems with payment on booking number {booking_id}, ' \
                           f'please, contact support team'
            create_and_assign_notification(
                Notification.REQUESTS,
                message_body,
                users_ids,
                Notification.BILLING,
                booking_id,
            )


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
            comment='Operation cancelled according to expired time for confirming booking by an agent',
            booking=operation,
        )


@celery_app.task(name='post_awb_number')
def send_awb_number_to_air_tracking_api(booking_number, booking_id, agent_contact_person_id):
    logger.info(f'Sending new airway bill number to track [{booking_number}]')
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
            message_body = f'The shipment {booking_number} cannot be tracked because of wrong booking number.'
            create_and_assign_notification.delay(
                Notification.OPERATIONS,
                message_body,
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

    logger.info(f'Response text for airway bill number [{booking_number}] - {response.text}')


@celery_app.task(name='track_sea_operations')
def track_confirmed_sea_operations():
    logger.info(f'Starting to get track statuses for confirmed operations')
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
                message_body = f'The shipment {operation.aceid} cannot be tracked because of wrong booking number.',
                create_and_assign_notification.delay(
                    Notification.OPERATIONS,
                    message_body,
                    [operation.agent_contact_person_id, ],
                    Notification.OPERATION,
                    object_id=operation.id,
                )
                client_email = [operation.agent_contact_person.email, ]
                send_email.delay(message_body, client_email,
                                 object_id=f'{settings.DOMAIN_ADDRESS}instance/{operation.id}')


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
                            message_body = f'The shipment {operation.aceid} has departed from {operation.freight_rate.origin}.'
                            create_and_assign_notification.delay(
                                Notification.OPERATIONS_IMPORT,
                                message_body,
                                [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                                Notification.OPERATION,
                                object_id=operation.id,
                            )
                            send_email.delay(message_body, [operation.agent_contact_person.email,
                                                            operation.client_contact_person.email, ],
                                             object_id=f'{settings.DOMAIN_ADDRESS}operation/{operation.id}')

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
                    message_body = f'The shipment {operation.aceid} has arrived at {operation.freight_rate.destination}.'
                    create_and_assign_notification.delay(
                        Notification.OPERATIONS_EXPORT,
                        message_body,
                        [operation.agent_contact_person_id, operation.client_contact_person_id, ],
                        Notification.OPERATION,
                        object_id=operation.id,
                    )
                    send_email.delay(message_body,
                                     [operation.agent_contact_person.email, operation.client_contact_person.email, ],
                                     object_id=f'{settings.DOMAIN_ADDRESS}operation/{operation.id}')

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
        message_body = 'Surcharges are about to expire. Please, extend its expiration rate ' \
                       'or create a new one with the updated costs.'
        create_and_assign_notification.delay(
            Notification.SURCHARGES,
            message_body,
            users_ids,
            Notification.SURCHARGE,
            object_id=surcharge.id,
        )
        users_emails = list(surcharge.company.role_set.filter(
            groups__name__in=('master', 'agent')
        ).values_list('user__emails', flat=True))
        send_email.delay(message_body, users_emails,
                         object_id=f'{settings.DOMAIN_ADDRESS}surcharge/{surcharge.id}')

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
            message_body = 'Surcharges are about to expire. Please, extend its expiration rate ' \
                           'or create a new one with the updated costs.'
            if user_email := user.email:
                send_email(
                    message_body,
                    [user_email, ],
                    object_id=f'{settings.DOMAIN_ADDRESS}surcharge/{surcharge.id}')  # TODO generate a link


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
        message_body = 'Rates are about to expire.Please, extend its expiration rate or create a new one with the updated costs.'
        create_and_assign_notification.delay(
            Notification.FREIGHT_RATES,
            message_body,
            users_ids,
            Notification.FREIGHT_RATE,
            object_id=freight_rate.id,
        )
        users_emails = list(freight_rate.company.role_set.filter(
            groups__name__in=('master', 'agent')
        ).values_list('user__emails', flat=True))
        send_email.delay(message_body, users_emails,
                         object_id=f'{settings.DOMAIN_ADDRESS}freight_rate/{freight_rate.id}')

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
            message_body = 'Rates are about to expire.Please, extend its expiration rate or create ' \
                           'a new one with the updated costs.'
            if user_email := user.email:
                send_email(message_body,
                           [user_email, ],
                           object_id=f'{settings.DOMAIN_ADDRESS}freight_rate/{freight_rate.id}')  # TODO generate a link


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
        message_body = f'The shipment {booking.aceid} is set to arrive in 3 days ' \
                       f'at {booking.freight_rate.destination}.'
        create_and_assign_notification.delay(
            Notification.OPERATIONS_IMPORT,
            message_body,
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
            message_body = f'The shipment {booking.aceid} is set to arrive in 3 days ' \
                           f'at {booking.freight_rate.destination}.'
            if email := user.email:
                send_email(message_body, [email, ],
                           object_id=f'{settings.DOMAIN_ADDRESS}operation/{booking.id}')  # TODO generate a link
