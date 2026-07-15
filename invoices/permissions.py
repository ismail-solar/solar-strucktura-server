# invoices/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnlyForOwner(BasePermission):
    """
    Admin: full access
    Normal user: read-only for their own invoices
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        # Everyone can read list/retrieve
        if request.method in SAFE_METHODS:
            return True

        # Only admin can create/update/delete
        return getattr(user, "role", None) == "admin"

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin can do anything
        if getattr(user, "role", None) == "admin":
            return True

        # Normal user: only read their own invoices
        if request.method in SAFE_METHODS:
            return obj.customer == user

        return False