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
from .models import CustomUser, FriendRequest, RequestStatus, UserProfile
from .utils import is_valid_email
from .permissions import IsReceiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from typing import Optional
from django.db.models import QuerySet


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


class UserSearchAPIView(APIView):
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
        user_profiles = UserProfile.objects.all().exclude(user=request.user)
        if search_key:
            search_vector = SearchVector('user__name')
            search_query = SearchQuery(search_key)
            user_profiles = user_profiles.annotate(search=search_vector).filter(search=search_query)
        paginator = CustomPagination()
        paginated_user_profiles = paginator.paginate_queryset(user_profiles, request)
        serializer = UserSerializer(paginated_user_profiles , many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FriendListView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet[UserProfile]:
        user_profile: UserProfile = self.request.user.user_profile
        return user_profile.get_friends()


class PendingRequestListView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet[FriendRequest]:
        user_profile = self.request.user.user_profile
        return FriendRequest.objects.filter(
            receiver=user_profile, status=RequestStatus.PENDING
        )


class SendRequestAPIview(APIView):
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
        pass

    def delete(self, request, block_detail_id):
        pass