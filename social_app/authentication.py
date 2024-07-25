from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model


class CustomAuthenticationBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email.lower())
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
