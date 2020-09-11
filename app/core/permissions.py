from rest_framework.permissions import BasePermission


class IsMaster(BasePermission):
    """
    Allows access only to users with role 'Master'.
    """

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated:
            return user.get_roles().filter(name='master').exists()
        return False
