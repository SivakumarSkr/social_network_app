from rest_framework.permissions import BasePermission
from .models import BlockDetail, FriendRequest


class IsReceiver(BasePermission):

    def has_permission(self, request, view) -> bool:
        return True

    def has_object_permission(self, request, view, obj) -> bool:
        if isinstance(obj, FriendRequest):
            return obj.receiver == request.user.user_profile
        return False


class IsNotBlockedUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        blocked = request.user.user_profile
        blocker_id = request.parser_context['kwargs'].get("user_id")
        return not BlockDetail.objects.filter(blocked=blocked, blocker_id=blocker_id).exists()
