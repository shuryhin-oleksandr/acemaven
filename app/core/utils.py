import random
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings

from app.core.models import Role, SignUpToken
from app.core.tasks import send_registration_email


def get_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def master_account_processing(company, email):
    user = get_user_model().objects.create(email=email)
    role = Role.objects.create(company=company, user=user)
    Group.objects.get(name='Master').users.add(role)
    sign_up_token = SignUpToken.objects.create(token=get_random_string(30), user=user)
    message_body = f'{settings.DOMAIN_ADDRESS}signup?token={sign_up_token.token}'
    send_registration_email.delay(message_body, user.email)
