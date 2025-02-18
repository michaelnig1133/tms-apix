from rest_framework.permissions import BasePermission

from auth_app.models import User

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.SYSTEM_ADMIN
    
class IsTransportManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.TRANSPORT_MANAGER