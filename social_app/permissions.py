from rest_framework.permissions import BasePermission
from .models import FriendRequest


class IsReceiver(BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, FriendRequest):
            return obj.receiver == request.user.user_profile
        return False