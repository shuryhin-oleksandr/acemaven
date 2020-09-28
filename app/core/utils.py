import random
import string

from django.contrib.auth import get_user_model

from app.core.models import Role, SignUpToken
from app.core.tasks import send_registration_email


def get_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def process_sign_up_token(user):
    sign_up_token = SignUpToken.objects.create(token=get_random_string(30), user=user)
    send_registration_email.delay(sign_up_token.token, user.email)


def master_account_processing(company, master_account_info):
    user = get_user_model().objects.create(**master_account_info)
    Role.objects.create(company=company, user=user)
    user.set_roles(['master'])
    process_sign_up_token(user)
