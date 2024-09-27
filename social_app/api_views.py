from abc import ABC, abstractmethod
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from django.db.models import Q
from django.db.utils import IntegrityError
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from social_app.helpers import process_request
from .serializers import (
    FriendRequestSerializer,
    SignUpSerializer,
    UserDetailSerializer,
    UserSerializer,
)
from rest_framework.pagination import PageNumberPagination
from .models import BlockDetail, CustomUser, FriendRequest, RequestStatus, UserProfile
from .utils import is_valid_email
from .permissions import IsNotBlockedUser, IsReceiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from typing import Optional
from django.db.models import QuerySet
from django.core.cache import cache
from rest_framework.filters import OrderingFilter

MAX_REQUESTS_ALLOWED = settings.MAX_REQUESTS_IN_MINUTE


class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request) -> Response:
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserSearchAPIView(generics.GenericAPIView):
    pagination_class = CustomPagination
    serializer_class = UserSerializer

    def __paginate_result(self, user_profiles):
        page = self.paginate_queryset(user_profiles)
        if page is not None:
            serializer = self.get_serializer(page , many=True)
            result = self.get_paginated_response(serializer.data)
            data = result.data
        else:
            serializer = self.get_serializer(user_profiles, many=True)
            data = serializer.data
        return data
    
    def get(self, request) -> Response:
        query_params = request.query_params
        search_key: Optional[str] = query_params.get("search", None)
        is_email: bool = is_valid_email(search_key)
        if is_email:
            user: CustomUser = get_object_or_404(CustomUser, email__iexact=search_key)
            user_profile_serializer: UserDetailSerializer = UserDetailSerializer(
                user.user_profile
            )
            return Response(
                data=user_profile_serializer.data, status=status.HTTP_200_OK
            )
        user_profiles = (
            UserProfile.objects.all().exclude(user=request.user)
            # remove users which blocked the current user
            .remove_block_users(request.user.user_profile)
        )
        if search_key:
            search_vector = SearchVector('user__name')
            search_query = SearchQuery(search_key)
            user_profiles = user_profiles.annotate(search=search_vector).filter(search=search_query)
        data = self.__paginate_result(user_profiles)
        return Response(data, status=status.HTTP_200_OK)


class BaseCachedListView(generics.ListAPIView):
    cache_key_prefix: Optional[str] = None  # Prefix for cache key (to be set in child classes)

    def get_cache_key(self, user_profile) -> str:
        return f"{self.cache_key_prefix}_{user_profile.uuid}"

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        user_profile = request.user.user_profile
        cache_key = self.get_cache_key(user_profile)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        cache.set(cache_key, response.data)
        return Response(response.data, status=status.HTTP_200_OK)


class FriendListView(BaseCachedListView):
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    cache_key_prefix = "friends_list"

    def get_queryset(self) -> QuerySet[UserProfile]:
        return UserProfile.objects.prefetch_related('friends').get(user=self.request.user).friends.all()


class PendingRequestListView(BaseCachedListView):
    serializer_class = FriendRequestSerializer
    pagination_class = CustomPagination
    cache_key_prefix = "pending_list"

    def get_queryset(self) -> QuerySet[FriendRequest]:
        return FriendRequest.objects.filter(
            receiver__user=self.request.user, status=RequestStatus.PENDING
        )


class SendRequestAPIview(APIView):
    permission_classes = [permissions.IsAuthenticated, IsNotBlockedUser]

    def post(self, request, user_id) -> Response:
        user_profile = request.user.user_profile
        time_threshold = timezone.now() - timedelta(seconds=60)
        requests_within_minute: int = FriendRequest.objects.filter(
            sender=user_profile, created_at__gte=time_threshold
        ).count()
        if requests_within_minute >= MAX_REQUESTS_ALLOWED:
            response: dict = {
                "message": f"Can't send more than {MAX_REQUESTS_ALLOWED} requests per minute."
            }
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)
        processed, response_dict = process_request(user_profile, user_id)
        return Response(
            data=response_dict,
            status=status.HTTP_200_OK if processed else status.HTTP_400_BAD_REQUEST,
        )


class BaseRequestView(APIView, ABC):
    """
    Base class for approve and reject apiViews.
    """

    permission_classes = [permissions.IsAuthenticated, IsReceiver]
    action: Optional[str] = None

    def put(self, request, request_id) -> Response:
        try:
            request_object: FriendRequest = FriendRequest.objects.select_related(
                "sender", "receiver"
            ).get(pk=request_id)
        except FriendRequest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, request_object)
        if request_object.not_in_pending():
            return Response(
                {"message": f"Request can't be {self.action}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_action(request_object)
        return Response(status=status.HTTP_200_OK)

    @abstractmethod
    def perform_action(self, request_object):
        """
        All API views inherit from this class should implement this method
        """
        pass


class ApproveRequestView(BaseRequestView):
    action = RequestStatus.ACCEPTED.label

    def perform_action(self, request_object: FriendRequest) -> None:
        request_object.make_accepted()


class RejectRequestView(BaseRequestView):
    action = RequestStatus.REJECTED.label

    def perform_action(self, request_object: FriendRequest) -> None:
        request_object.make_rejected()


class BlockUnBlockAPIView(APIView):
    def post(self, request, user_id):
        user_profile = request.user.user_profile
        try:
            BlockDetail.objects.create(blocker=user_profile, blocked_id=user_id)
        except IntegrityError:
            return Response({"message": "Already blocked"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Blocked Successfully"})

    def delete(self, request, user_id):
        user_profile = request.user.user_profile
        blocked_detail = BlockDetail.objects.filter(blocker=user_profile, blocked_id=user_id).first()
        if blocked_detail is None:
            return Response({"message": "User not blocked"}, status=status.HTTP_400_BAD_REQUEST)
        blocked_detail.delete()
        return Response({"message": "User is unblocked"})
