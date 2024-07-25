import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from social_app.models import UserProfile
from django.core.exceptions import ValidationError


User = get_user_model()


@pytest.fixture
def user_and_profiles():
    # Create a user and associated user profile
    user1 = User.objects.create_user(email='user1@example.com', password='password123', name='User One')
    profile1 = UserProfile.objects.create(user=user1)
    user2 = User.objects.create_user(email='user2@example.com', password='password123', name='User Two')
    profile2 = UserProfile.objects.create(user=user2)
    return {
        'user1': user1,
        'profile1': profile1,
        'user2': user2,
        'profile2': profile2
    }


@pytest.fixture
def authenticated_client(user_and_profiles):
    client = APIClient()
    client.force_authenticate(user=user_and_profiles['user1'])
    return client


@pytest.mark.django_db
def test_user_search_by_email(authenticated_client, user_and_profiles):
    url = reverse('users')  # Update with the actual URL pattern name
    response = authenticated_client.get(url, {'search': 'user2@example.com'})
    assert response.status_code == status.HTTP_200_OK
    assert response.data['email'] == 'user2@example.com'
    response = authenticated_client.get(url, {'search': 'User2@Example.com'})
    assert response.status_code == status.HTTP_200_OK
    assert response.data['email'] == 'user2@example.com'


@pytest.mark.django_db
def test_user_search_by_name(authenticated_client, user_and_profiles):
    url = reverse('users')  # Update with the actual URL pattern name
    response = authenticated_client.get(url, {'search': 'User Two'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0
    assert any(user['name'] == 'User Two' for user in response.data)
    response = authenticated_client.get(url, {'search': 'user'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0
    assert any(user['name'] == 'User Two' for user in response.data)


@pytest.mark.django_db
def test_user_search_no_results(authenticated_client):
    url = reverse('users')  # Update with the actual URL pattern name
    response = authenticated_client.get(url, {'search': 'nonexistent@example.com'})
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_user_search_authenticated_user_excluded(authenticated_client, user_and_profiles):
    url = reverse('users')  # Update with the actual URL pattern name
    response = authenticated_client.get(url, {'search': 'User One'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0
