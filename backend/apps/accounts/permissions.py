from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an administrator
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsAgent(permissions.BasePermission):
    """
    Permission class to check if user is a sales agent
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'AGENT'
        )


class IsAdminOrAgent(permissions.BasePermission):
    """
    Permission class to check if user is either admin or agent
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'AGENT']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class to check if user is the owner of the object or an admin
    """

    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.role == 'ADMIN':
            return True

        # Check if the object has a user or created_by field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows admins to edit, but others can only read
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to admins
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )
