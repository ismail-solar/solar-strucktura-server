# plans/permission.py
from rest_framework.permissions import BasePermission

class IsCustomAdmin(BasePermission):
    """
    Allows access only to users with role='admin'.
    """

    def has_permission(self, request, view):
        user = request.user
        # Make sure user is authenticated and has role 'admin'
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'admin')