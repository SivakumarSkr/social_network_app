from rest_framework import serializers
from .models import CustomUser, UserProfile, FriendRequest

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ('name', 'email', 'password')


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, source='user.name')
    class Meta:
        model = UserProfile
        fields = ('uuid', 'name')


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, source='user.name')
    class Meta:
        model = UserProfile
        fields = ('uuid', 'email', 'name')


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ('uuid', 'status', 'sender', 'created_at')
