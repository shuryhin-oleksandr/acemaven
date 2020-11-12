from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from app.core.models import SignUpToken


class CheckTokenMixin:
    """
    Class, that provides custom get_object() method.
    """

    def get_object(self):
        token = self.request.query_params.get('token')
        obj = get_object_or_404(SignUpToken.objects.all(), token=token)
        return obj


class CreateMixin:
    """
    Class, that provides custom create() method for bulk object creation optionally.
    """

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PermissionClassByActionMixin:
    """
   Mixed permission base model allowing for action level
   permission control. Subclasses may define their permissions
   by creating a 'permission_classes_by_action' variable.

   Example:
   permission_classes_by_action = {'list': [AllowAny],
                                   'create': [IsAdminUser]}
   """

    permission_classes_by_action = {}

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]
