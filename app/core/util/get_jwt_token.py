from django.contrib.auth import get_user_model
from rest_framework_jwt.serializers import jwt_payload_handler

from rest_framework_jwt.utils import jwt_encode_handler

User = get_user_model()


def get_jwt_token(user: User):
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return token
