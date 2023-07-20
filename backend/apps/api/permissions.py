from rest_framework import permissions


class AuthorOrReadOnly(permissions.BasePermission):
    """
    Any - read.
    Author - read, update.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class NotBlockedUser(permissions.BasePermission):
    """Blocked user don't have permission."""
    def has_permission(self, request, view):
        user = request.user
        return not user.is_authenticated or not user.is_blocked