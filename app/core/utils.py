import random
import string

from django.contrib.auth import get_user_model
from django.db.models import Avg

from app.core.models import Role, SignUpToken, EmailNotificationSetting
from app.core.tasks import send_registration_email


def get_random_string(length):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def process_sign_up_token(user):
    sign_up_token = SignUpToken.objects.create(token=get_random_string(30), user=user)
    send_registration_email.delay(sign_up_token.token, user.email)


def master_account_processing(company, master_account_info):
    user = get_user_model().objects.filter(**master_account_info).first()
    if not user:
        user = get_user_model().objects.create(**master_account_info)
    role = Role.objects.filter(company=company, user=user)
    if not role:
        Role.objects.create(company=company, user=user)
        user.set_roles(['master'])
    EmailNotificationSetting.objects.create(user=user)
    process_sign_up_token(user)


def choice_to_value_name(choices):
    value_name_list = []
    for value, name in choices:
        value_name_list.append({'id': value, 'title': name})
    return value_name_list


def get_average_company_rating(company):
    average_rating = company.get_reviews().aggregate(average_rating=Avg('rating')).get('average_rating')
    return average_rating
