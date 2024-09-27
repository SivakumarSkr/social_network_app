from django.urls import path
from .api_views import (
    BlockUnBlockAPIView,
    SignUpView,
    UserSearchAPIView,
    FriendListView,
    SendRequestAPIview,
    PendingRequestListView,
    ApproveRequestView,
    RejectRequestView,
)


urlpatterns = [
    path("signup/", SignUpView.as_view(), name="sign-up"),
    path("users/", UserSearchAPIView.as_view(), name="users"),
    path("friend-list/", FriendListView.as_view(), name="friend-list"),
    path(
        "pending-requests/", PendingRequestListView.as_view(), name="pending-requests"
    ),
    path(
        "user/<user_id>/send-request/",
        SendRequestAPIview.as_view(),
        name="send-requests",
    ),
    path(
        "request/<request_id>/accept/",
        ApproveRequestView.as_view(),
        name="accept-request",
    ),
    path(
        "request/<request_id>/reject/",
        RejectRequestView.as_view(),
        name="reject-request",
    ),
    path("block/<user_id>/", BlockUnBlockAPIView.as_view(), name="block-unblock")
]
