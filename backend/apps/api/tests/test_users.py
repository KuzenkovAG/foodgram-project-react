from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from ...recipes import models

User = get_user_model()


class UserApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_data = {
            "email": "test_user@mail.ru",
            "username": "test_user",
            "first_name": "test",
            "last_name": "user",
            "password": make_password("Qwerty123")
        }
        cls.user = User.objects.create(**user_data)
        token = Token.objects.create(user=cls.user).key
        cls.headers_authorized = {
            'Authorization': f"Token {token}"
        }
        author_data = {
            "email": "follower@mail.ru",
            "username": "follower",
            "first_name": "follower",
            "last_name": "follower",
            "password": make_password("Qwerty123")
        }
        cls.author = User.objects.create(**author_data)
        models.Follow.objects.create(
            author=cls.author,
            follower=cls.user
        )

    def test_get_user_list(self):
        """Get users list. Permissions - Any."""
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user(self):
        """Create new user. Permissions - Any."""
        url = reverse('user-list')
        new_user = {
            "email": "vpupkin@yandex.ru",
            "username": "vasya4.pupkin",
            "first_name": "Вася",
            "last_name": "Пупкин",
            "password": "Qwerty123"
        }
        response = self.client.post(url, data=new_user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_user_retrieve_authorized_user(self):
        """Get user by id. Permissions - IsAuthorized."""
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        expected_data = {
            "id": self.user.id,
            "email": "test_user@mail.ru",
            "username": "test_user",
            "first_name": "test",
            "last_name": "user",
            "is_subscribed": False
        }
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_get_user_retrieve_not_authorized_user(self):
        """Get user by id not allow for not authorized user."""
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_current_user_authorized_user(self):
        """Get current user. Permissions - Authorized."""
        url = reverse('user-me')
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_current_user_not_authorized_user(self):
        """Get current user not available for not authorized user."""
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_not_authorized_user(self):
        """Password change not available for not authorized user."""
        url = reverse('user-change-password')
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_authorized_user(self):
        """
        Password can change only if current password is correct.
        Permission - Authorized.
        """
        url = reverse('user-change-password')
        new_password = {
            "new_password": "NewPassword",
            "current_password": "Qwerty123"
        }
        wrong_password = {
            "new_password": "NewPassword",
            "current_password": "Qwerty1232"
        }
        response = self.client.post(
            url, data=wrong_password, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url, data=new_password, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_users_list_is_subscribed_value(self):
        """Check what user have the correct is_subscribed value."""
        url = reverse('user-list')
        response = self.client.get(url, headers=self.headers_authorized)
        expected_data = [
            {
                "id": self.user.id,
                "email": self.user.email,
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_subscribed": False
            },
            {
                "id": self.author.id,
                "email": self.author.email,
                "username": self.author.username,
                "first_name": self.author.first_name,
                "last_name": self.author.last_name,
                "is_subscribed": True
            }
        ]
        self.assertEqual(response.data.get('results'), expected_data)


class UserPaginatorApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        users_list = [
            User(
                email='test_user@mail.ru',
                username=f'test_user{i}',
                first_name='test',
                last_name='user',
                password="Qwerty123"
            ) for i in range(1, 21)
        ]
        cls.users = User.objects.bulk_create(users_list)
        cls.expected_results = [
            {
                "id": i,
                "email": "test_user@mail.ru",
                "username": f'test_user{i}',
                "first_name": "test",
                "last_name": "user",
                "is_subscribed": False
            } for i in range(1, 21)
        ]

    def test_get_user_list_pagination(self):
        """Check pagination in user list."""
        url = reverse('user-list')
        response = self.client.get(url)
        results = response.data.get('results')
        self.assertEqual(results, self.expected_results[:6])

    def test_get_user_list_pagination_with_page_param(self):
        """Check pagination in user list."""
        url = reverse('user-list')
        url += '?page=2'
        response = self.client.get(url)
        results = response.data.get('results')
        self.assertEqual(results, self.expected_results[6:12])

    def test_get_user_list_pagination_with_limit_param(self):
        """Check pagination with parameter - limit."""
        url = reverse('user-list')
        url += '?limit=5'
        response = self.client.get(url)
        results = response.data.get('results')
        self.assertEqual(results, self.expected_results[:5])


class TokenApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_data = {
            "email": "test_user@mail.ru",
            "username": "test_user",
            "first_name": "test",
            "last_name": "user",
            "password": make_password("Qwerty123")
        }
        cls.user = User.objects.create(**user_data)
        cls.token = Token.objects.create(user=cls.user).key

    def test_receive_token(self):
        """Login - Receive token."""
        url = '/api/v1/auth/token/login/'
        login_data = {
            'email': 'test_user@mail.ru',
            'password': 'Qwerty123'
        }
        response = self.client.post(url, data=login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('auth_token'), self.token)

    def test_remove_token(self):
        """Logout - remove token."""
        url = '/api/v1/auth/token/logout/'
        headers = {
            'Authorization': f"Token {self.token}"
        }
        response = self.client.post(url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
