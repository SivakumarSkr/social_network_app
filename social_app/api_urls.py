from django.urls import path
from .api_views import SignUpView, UserSearchAPIView, FriendListView, SendRequestAPIview, PendingRequestListView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='sign-up'),
    path('users/', UserSearchAPIView.as_view(), name='users'),
    path('friend-list/', FriendListView.as_view(), name='friend-list'),
    path('pending-requests/', PendingRequestListView.as_view(), name='pending-requests'),
    path('user/<user_id>/send-request/', SendRequestAPIview.as_view(), name='send-requests'),
]