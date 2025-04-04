from auth_app import permissions


class IsAllowedVehicleUser(permissions.BasePermission):
    """
    Custom permission to allow only specific roles to access the assigned vehicle.
    """

    ALLOWED_ROLES = {2, 3, 4, 5, 6}  # Allowed roles: Department Manager, Finance Manager, Transport Manager, CEO, Driver

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.ALLOWED_ROLES