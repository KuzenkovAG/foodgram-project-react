import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, override_settings

from ...recipes import models

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SubscriptionAPITestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            email='author@mail.ru',
            username='author',
            first_name='Authorov',
            last_name='Author',
        )
        cls.user = User.objects.create(
            email='user@mail.ru',
            username='user',
        )
        token_user = Token.objects.create(user=cls.user).key
        cls.headers_authorized = {
            'Authorization': f"Token {token_user}"
        }
        recipes = [
            models.Recipe(
                author=cls.author,
                name='Рецепт',
                image='image.jpeg',
                text='Рецепт',
                cooking_time=1
            ) for _ in range(10)
        ]
        cls.recipes = models.Recipe.objects.bulk_create(recipes)

        models.Follow.objects.create(
            author=cls.author,
            follower=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_get_user_subscription_not_authorized(self):
        """Get subsctiption for not authorized user."""
        url = reverse('user-get-subscriptions')
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            'Unauthorized user can not get subscriptions'
        )

    def test_get_user_subscription_authorized_user(self):
        """Get subsctiption for not authorized user."""
        url = reverse('user-get-subscriptions')
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_subscription_with_recipes_limit_param(self):
        """Get subsctiption with parameter - recipes_limit."""
        expected_recipe_count = models.Recipe.objects.filter(
            author=self.author
        ).count()
        recipes_limit = 3
        url = reverse('user-get-subscriptions')
        url += f'?recipes_limit={recipes_limit}'
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results')[0]
        recipes = results.get('recipes')
        self.assertEqual(len(recipes), recipes_limit)
        recipes_count = results.get('recipes_count')
        self.assertEqual(recipes_count, expected_recipe_count)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SubscriptionPaginationAPITestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            email='author@mail.ru',
            username='author',
            first_name='Authorov',
            last_name='Author',
        )
        cls.another_author = User.objects.create(
            email='other_author@mail.ru',
            username='other',
            first_name='Other',
            last_name='Other',
        )
        cls.user = User.objects.create(
            email='user@mail.ru',
            username='user',
        )
        token_user = Token.objects.create(user=cls.user).key
        cls.headers_authorized = {
            'Authorization': f"Token {token_user}"
        }
        models.Follow.objects.create(
            author=cls.author,
            follower=cls.user
        )
        models.Follow.objects.create(
            author=cls.another_author,
            follower=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_get_subscription_pagination_with_limit_param(self):
        """Check pagination in subscription."""
        url = reverse('user-get-subscriptions')
        limit = 1
        url += f'?limit={limit}'
        response = self.client.get(url, headers=self.headers_authorized)
        results = response.data.get('results')
        self.assertEqual(
            len(results),
            limit,
            'Unexpected result len.'
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SubscribeAPITestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            email='author@mail.ru',
            username='author',
            first_name='Authorov',
            last_name='Author',
        )
        cls.follow_user = User.objects.create(
            email='follow_user@mail.ru',
            username='follow_user',
            first_name='Follow',
            last_name='Follow',
        )
        cls.user = User.objects.create(
            email='user@mail.ru',
            username='user',
        )
        token_user = Token.objects.create(user=cls.user).key
        cls.headers_authorized = {
            'Authorization': f"Token {token_user}"
        }
        models.Follow.objects.create(
            author=cls.follow_user,
            follower=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_subscribe_not_authorized_user(self):
        """Test case: not authorized user subscribe on author."""
        url = reverse('user-subscribe', kwargs={'pk': self.author.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unsubscribe_not_authorized_user(self):
        """Test case: not authorized user unsubscribe on author."""
        url = reverse('user-subscribe', kwargs={'pk': self.author.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscribe_authorized_user(self):
        """Test case - user unsubscribe and subscribe on author."""
        url = reverse('user-subscribe', kwargs={'pk': self.author.id})
        response = self.client.delete(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'User can not unsubscribe if not subscribed on author'
        )
        response = self.client.post(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            'User can subscribed on author'
        )

    def test_subscribe_on_yourself(self):
        """Test case - user subscribe on yourself."""
        url = reverse('user-subscribe', kwargs={'pk': self.user.id})
        response = self.client.post(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'User can subscribe on yourself'
        )

    def test_subscribe_on_non_exsisted_user(self):
        """Test case - user subscribe on non-existed user."""
        url = reverse('user-subscribe', kwargs={'pk': 9999})
        response = self.client.post(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'User can not subscribe on non-existed user.'
        )

    def test_unsubscribe_on_non_exsisted_user(self):
        """Test case - user unsubscribe on non-existed user."""
        url = reverse('user-subscribe', kwargs={'pk': 9999})
        response = self.client.delete(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'User can not unsubscribe from non-existed user.'
        )

    def test_unsubscribe_authorized_user(self):
        """Test case - user subscribe and unsubscribe on author."""
        url = reverse('user-subscribe', kwargs={'pk': self.follow_user.id})
        response = self.client.post(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'User can not subscribe if author already subscribed'
        )
        response = self.client.delete(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
            'User can unsubscribe from author.'
        )
