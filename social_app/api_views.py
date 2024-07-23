from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from django.db.models import Q
from django.db.utils import IntegrityError
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from .serializers import FriendRequestSerializer, SignUpSerializer, UserDetailSerializer, UserSerializer
from .models import CustomUser, FriendRequest, RequestStatus, UserProfile
from .utils import is_valid_email
from django.utils import timezone
from django.conf import settings


MAX_REQUESTS_ALLOWED = settings.MAX_REQUESTS_IN_MINUTE
# Create your views here.
class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSearchAPIView(APIView):
    def get(self, request, *args, **kwargs):
        query_params = request.query_params
        search_key = query_params.get('search', None)
        is_email = is_valid_email(search_key)
        if is_email:
            user = get_object_or_404(CustomUser, email=search_key)
            user_profile_serializer = UserDetailSerializer(user.user_profile)
            return Response(data=user_profile_serializer.data, status=status.HTTP_200_OK)
        user_profiles = UserProfile.objects.filter(Q(user__email__icontains=search_key) | Q(user__name__icontains=search_key))
        serializer = UserSerializer(user_profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FriendListView(generics.ListAPIView):
    serializer_class = UserSerializer
    def get_queryset(self):
        user_profile = self.request.user.user_profile
        return user_profile.get_friends()


class PendingRequestListView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    def get_queryset(self):
        user_profile = self.request.user.user_profile
        return FriendRequest.objects.filter(receiver=user_profile, status=RequestStatus.PENDING)


class SendRequestAPIview(APIView):
    def post(self, request, user_id):
        user_profile = request.user.user_profile
        time_threshold = timezone.now() - timezone.timedelta(seconds=60)
        requests_within_minute = FriendRequest.objects.filter(
            sender=user_profile, created_at__gte=time_threshold
        ).count()
        if requests_within_minute >= MAX_REQUESTS_ALLOWED:
            response = {
                "message": f"Can't send more than {MAX_REQUESTS_ALLOWED} requests"
            }
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)
        try:
            requests_object = FriendRequest.objects.create(
                sender=user_profile,
                receiver_id=user_id
            )
            return Response(
                data=FriendRequestSerializer(requests_object).data, 
                status=status.HTTP_200_OK
            )
        except IntegrityError:
            return Response(
                data={"message": "Friend Request to this user is already present"},
                status=status.HTTP_400_BAD_REQUEST
            )