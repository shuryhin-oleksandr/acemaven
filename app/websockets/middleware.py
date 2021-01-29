from urllib import parse

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    try:
        token = {'token': token_key}
        valid_data = VerifyJSONWebTokenSerializer().validate(token)
        user = valid_data['user']
        print(str(user))
        return user
    except Exception as e:
        return AnonymousUser()


class TokenAuthMiddlewareInstance:
    def __init__(self, scope):
        self.scope = dict(scope)

    async def resolve_user(self):
        query = parse.parse_qs(self.scope['query_string'].decode())
        try:
            token_key = query['token'][0]
            print(token_key)
        except Exception as e:
            print(e)
            token_key = None

        self.scope['user'] = await get_user(token_key)


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        wrapper = TokenAuthMiddlewareInstance(scope)
        print(scope, receive, send)
        await wrapper.resolve_user()

        return await self.inner(wrapper.scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
