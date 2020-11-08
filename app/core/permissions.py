from rest_framework.permissions import BasePermission

from django.db.models import Q


class IsMaster(BasePermission):
    """
    Allows access only to users with role 'Master'.
    """

    def has_permission(self, request, view):
        if request.user.role_set.exists():
            return request.user.get_roles().filter(name='master').exists()
        return False


class IsBilling(BasePermission):
    """
    Allows access only to users with role 'Billing'.
    """

    def has_permission(self, request, view):
        if request.user.role_set.exists():
            return request.user.get_roles().filter(name='billing').exists()
        return False


class IsMasterOrBilling(BasePermission):
    """
    Allows access only to users with role 'Master' or 'Billing'.
    """

    def has_permission(self, request, view):
        if request.user.role_set.exists():
            return request.user.get_roles().filter(Q(name='master') | Q(name='billing')).exists()
        return False


class IsMasterOrAgent(BasePermission):
    """
    Allows access only to users with role 'Master' or 'Agent'.
    """

    def has_permission(self, request, view):
        if request.user.role_set.exists():
            return request.user.get_roles().filter(Q(name='master') | Q(name='agent')).exists()
        return False


class IsClientCompany(BasePermission):
    """
    Allows access only to users with role 'Master' or 'Billing' or 'Client'.
    """

    def has_permission(self, request, view):
        if request.user.role_set.exists():
            return request.user.get_roles().filter(Q(name='master') | Q(name='billing') | Q(name='client')).exists()
        return False
