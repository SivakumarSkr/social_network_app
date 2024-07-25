from rest_framework import serializers
from .models import CustomUser, UserProfile, FriendRequest
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = CustomUser
        fields = ("name", "email", "password")

    def validate_password(self, value):
        # Validate password using Django's built-in validators
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate_email(self, value):
        value = value.lower()
        try:
            CustomUser.objects.get(email=value)
            raise serializers.ValidationError("User with this email already exisits")
        except CustomUser.DoesNotExist:
            return value
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            name=validated_data["name"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        UserProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, source="user.name")

    class Meta:
        model = UserProfile
        fields = ("uuid", "name")


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, source="user.name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = UserProfile
        fields = ("uuid", "email", "name")


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = FriendRequest
        fields = ("uuid", "status", "sender", "created_at")
