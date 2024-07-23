from django.urls import path
from .api_views import SignUpView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='sign-up'),
]