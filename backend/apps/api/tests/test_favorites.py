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
class FavoriteRecipeAPITestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            email='user@mail.ru',
            username='user',
        )
        token_user = Token.objects.create(user=cls.user).key
        cls.headers_authorized = {
            'Authorization': f"Token {token_user}"
        }
        cls.recipe = models.Recipe.objects.create(
            author=cls.user,
            name='Рецепт.',
            image='image.jpeg',
            text='Обычный рецепт...',
            cooking_time=60
        )
        cls.recipe_favorite = models.Recipe.objects.create(
            author=cls.user,
            name='Избранный Рецепт.',
            image='image.jpeg',
            text='Супер рецепт.',
            cooking_time=60
        )
        cls.recipe_not_favorite = models.Recipe.objects.create(
            author=cls.user,
            name='Рецепт не из избранного.',
            image='image.jpeg',
            text='Не избранный.',
            cooking_time=60
        )
        cls.recipe_favorite_for_removing = models.Recipe.objects.create(
            author=cls.user,
            name='Избрынный рецепт для удаления.',
            image='image.jpeg',
            text='Не плохой рецепт.',
            cooking_time=60
        )
        models.Favorite.objects.create(
            user=cls.user,
            recipe=cls.recipe_favorite
        )
        models.Favorite.objects.create(
            user=cls.user,
            recipe=cls.recipe_favorite_for_removing
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_add_recipe_to_favorite_unauthorized_user(self):
        """Unauthorized user can not add recipe to favorite."""
        url = reverse('recipe-manage-favorites', kwargs={'pk': self.recipe.id})
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_recipe_to_favorite(self):
        """User can add recipe to favorite."""
        favorite_before = models.Favorite.objects.filter(
            user=self.user).count()
        url = reverse('recipe-manage-favorites', kwargs={'pk': self.recipe.id})
        response = self.client.post(
            url,
            headers=self.headers_authorized
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        favorite_after = models.Favorite.objects.filter(user=self.user).count()
        self.assertEqual(
            favorite_before,
            favorite_after - 1,
            'Favorite was not added'
        )
        expected_data = {
            'id': 1,
            'name': 'Рецепт.',
            'image': '/media/image.jpeg',
            'cooking_time': 60
        }
        self.assertEqual(response.data, expected_data)

    def test_add_recipe_what_already_have(self):
        """User can not add recipe what already in favorite."""
        favorite_before = models.Favorite.objects.filter(
            user=self.user,
            recipe=self.recipe_favorite
        ).count()
        url = reverse(
            'recipe-manage-favorites',
            kwargs={'pk': self.recipe_favorite.id}
        )
        response = self.client.post(url, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,)
        favorite_after = models.Favorite.objects.filter(
            user=self.user,
            recipe=self.recipe_favorite
        ).count()
        self.assertEqual(
            favorite_before,
            favorite_after,
            'User can not add recipe in favorite'
        )

    def test_remove_recipe_from_favorite_unauthorized_user(self):
        """Unauthorized user can not remove recipe."""
        url = reverse('recipe-manage-favorites', kwargs={'pk': self.recipe.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_recipe_what_not_in_favorite(self):
        """User can't remove recipe what not in favorite."""
        url = reverse(
            'recipe-manage-favorites',
            kwargs={'pk': self.recipe_favorite_for_removing.id}
        )
        response = self.client.delete(url, headers=self.headers_authorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
            'Recipe can not be removed'
        )
        favorite = models.Favorite.objects.filter(
            user=self.user,
            recipe=self.recipe_favorite_for_removing
        )
        self.assertFalse(
            favorite.exists(),
            'Recipe not removed.'
        )
