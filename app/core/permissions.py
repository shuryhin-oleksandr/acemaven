from rest_framework.permissions import BasePermission

from django.db.models import Q


class IsMaster(BasePermission):
    """
    Allows access only to users with role 'Master'.
    """

    def has_permission(self, request, view):
        return request.user.get_roles().filter(name='master').exists()


class IsBilling(BasePermission):
    """
    Allows access only to users with role 'Billing'.
    """

    def has_permission(self, request, view):
        return request.user.get_roles().filter(name='billing').exists()


class IsMasterOrBilling(BasePermission):
    """
    Allows access only to users with role 'Master' or 'Billing'.
    """

    def has_permission(self, request, view):
        return request.user.get_roles().filter(Q(name='master') | Q(name='billing')).exists()
