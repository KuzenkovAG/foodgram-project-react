import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, override_settings

from ...recipes import models

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipeApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_data = {
            'email': 'test_user@mail.ru',
            'username': 'test_user',
            'first_name': 'test',
            'last_name': 'user',
            'password': make_password('Qwerty123')
        }
        cls.user = User.objects.create(**user_data)
        token_user = Token.objects.create(user=cls.user).key
        cls.headers_authorized = {
            'Authorization': f"Token {token_user}"
        }
        author_data = {
            'email': 'author@mail.ru',
            'username': 'recipe_author',
            'first_name': 'author',
            'last_name': 'author',
            'password': make_password('Qwerty123')
        }
        cls.author = User.objects.create(**author_data)
        token_author = Token.objects.create(user=cls.author).key
        cls.headers_authorized_author = {
            'Authorization': f"Token {token_author}"
        }
        ingredient = models.Ingredient.objects.create(
            name='Картофель отварной',
            measurement_unit='г'
        )
        cls.recipe = models.Recipe.objects.create(
            author=cls.author,
            name='Картофель отварной.',
            image='image.jpeg',
            text='Возьмите столовую ложку...',
            cooking_time=10
        )
        cls.recipe_ingredients = models.IngredientAmount.objects.create(
            ingredient=ingredient,
            amount=1
        )
        cls.tag = models.Tag.objects.create(
            name='Обед',
            color='#ffffff',
            slug='diner'
        )
        cls.recipe.tags.add(cls.tag)
        cls.recipe.ingredients.add(cls.recipe_ingredients)
        models.ShoppingCart.objects.create(
            user=cls.user,
            recipe=cls.recipe
        )
        models.Favorite.objects.create(
            user=cls.user,
            recipe=cls.recipe
        )
        models.Follow.objects.create(
            author=cls.author,
            follower=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_get_recipe_list(self):
        """Get list of recipes."""
        expected_data = [
            {
                "id": self.recipe.id,
                "tags": [
                    {
                        'id': self.tag.id,
                        'name': 'Обед',
                        'color': '#ffffff',
                        'slug': 'diner'
                    }
                ],
                "author": {
                    "id": self.author.id,
                    "email": "author@mail.ru",
                    "username": "recipe_author",
                    "first_name": "author",
                    "last_name": "author",
                    "is_subscribed": True
                },
                "ingredients": [
                    {
                        "id": self.recipe_ingredients.id,
                        "name": "Картофель отварной",
                        "measurement_unit": "г",
                        "amount": 1
                    }
                ],
                "is_favorited": True,
                "is_in_shopping_cart": True,
                "name": "Картофель отварной.",
                "image": "http://testserver/media/image.jpeg",
                "text": "Возьмите столовую ложку...",
                "cooking_time": 10
            }
        ]
        expected_data = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": expected_data
        }
        url = reverse('recipe-list')
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_create_recipe_unauthorized_user(self):
        """Create recipe by unauthorized users."""
        url = reverse('recipe-list')
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_recipe_authorized_user(self):
        """Create recipe by authorized users."""
        post_data = {
            "image": "data:image/jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
            "name": "Суп",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 10,
            "ingredients": [
                {
                    "id": self.recipe_ingredients.id,
                    "amount": 1
                }
            ],
            'tags': [self.tag.id],
        }
        expected_data = {
            "id": 2,
            "tags": [
                {
                    'id': self.tag.id,
                    'name': 'Обед',
                    'color': '#ffffff',
                    'slug': 'diner'
                }
            ],
            "author": {
                "id": self.user.id,
                "email": "test_user@mail.ru",
                "username": "test_user",
                "first_name": "test",
                "last_name": "user",
                "is_subscribed": False
            },
            "ingredients": [
                {
                    "id": 2,
                    "name": "Картофель отварной",
                    "measurement_unit": "г",
                    "amount": 1
                }
            ],
            "is_favorited": False,
            "is_in_shopping_cart": False,
            "name": "Суп",
            "image": "http://testserver/media/recipes/temp.jpg",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 10
        }
        url = reverse('recipe-list')
        response = self.client.post(
            url,
            data=post_data,
            format='json',
            headers=self.headers_authorized
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, expected_data)

    def test_create_recipe_with_wrong_image(self):
        """Creation recipe with wrong image format."""
        url = reverse('recipe-list')
        wrong_data = {
            "image": "dat:image/jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
            "name": "Суп",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 10,
            "ingredients": [
                {
                    "id": self.recipe_ingredients.id,
                    "amount": 1
                }
            ],
            'tags': [self.tag.id],
        }
        response = self.client.post(
            url,
            data=wrong_data,
            format='json',
            headers=self.headers_authorized
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_wrong_amount_format(self):
        """Creation recipe with wrong amount format."""
        url = reverse('recipe-list')
        wrong_data = {
            "image": "data:image/jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
            "name": "Суп",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 10,
            "ingredients": [
                {
                    "id": self.recipe_ingredients.id,
                    "amount": 'one'
                }
            ],
            'tags': [self.tag.id],
        }
        response = self.client.post(
            url,
            data=wrong_data,
            format='json',
            headers=self.headers_authorized
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_wrong_cooking_time_format(self):
        """Creation recipe with wrong cooking time format."""
        url = reverse('recipe-list')
        wrong_data = {
            "image": "data:image/jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
            "name": "Суп",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 'ten minutes',
            "ingredients": [
                {
                    "id": self.recipe_ingredients.id,
                    "amount": 1
                }
            ],
            'tags': [self.tag.id],
        }
        response = self.client.post(
            url,
            data=wrong_data,
            format='json',
            headers=self.headers_authorized
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_wrong_tag_id(self):
        """Creation recipe with wrong tag id."""
        url = reverse('recipe-list')
        wrong_data = {
            "image": "data:image/jpg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
            "name": "Суп",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 10,
            "ingredients": [
                {
                    "id": self.recipe_ingredients.id,
                    "amount": 1
                }
            ],
            'tags': [3],
        }
        response = self.client.post(
            url,
            data=wrong_data,
            format='json',
            headers=self.headers_authorized
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_recipe_by_id(self):
        """Get recipe by id."""
        expected_data = {
            "id": 1,
            "tags": [
                {
                    'id': self.tag.id,
                    'name': 'Обед',
                    'color': '#ffffff',
                    'slug': 'diner'
                }
            ],
            "author": {
                "id": self.author.id,
                "email": self.author.email,
                "username": self.author.username,
                "first_name": self.author.first_name,
                "last_name": self.author.last_name,
                "is_subscribed": False
            },
            "ingredients": [
                {
                    "id": 1,
                    "name": "Картофель отварной",
                    "measurement_unit": "г",
                    "amount": 1
                }
            ],
            "is_favorited": False,
            "is_in_shopping_cart": False,
            "name": "Картофель отварной.",
            "image": "http://testserver/media/image.jpeg",
            "text": "Возьмите столовую ложку...",
            "cooking_time": 10
        }
        url = reverse('recipe-detail', kwargs={'pk': self.recipe.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_update_recipe_unauthorized_user(self):
        """Update recipe by unauthorized user."""
        url = reverse('recipe-detail', kwargs={'pk': self.recipe.id})
        response = self.client.patch(url, data={})
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Unauthorized user can't update recipe"
        )

    def test_update_recipe_not_owner_user(self):
        """Update recipe by authorized user but not owner."""
        url = reverse('recipe-detail', kwargs={'pk': self.recipe.id})
        response = self.client.patch(
            url,
            data={},
            headers=self.headers_authorized
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Authorized user can't update not own recipe"
        )

    def test_update_recipe_by_owner(self):
        """Update recipe by owner."""
        post_data = {
            "name": "Суп",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 20,
            "ingredients": [
                {
                    "id": self.recipe_ingredients.id,
                    "amount": 1
                }
            ],
            'tags': [self.tag.id],
        }
        expected_data = {
            "id": 1,
            "tags": [
                {
                    'id': self.tag.id,
                    'name': 'Обед',
                    'color': '#ffffff',
                    'slug': 'diner'
                }
            ],
            "author": {
                "id": self.author.id,
                "email": self.author.email,
                "username": self.author.username,
                "first_name": self.author.first_name,
                "last_name": self.author.last_name,
                "is_subscribed": False
            },
            "ingredients": [
                {
                    "id": 2,
                    "name": "Картофель отварной",
                    "measurement_unit": "г",
                    "amount": 1
                }
            ],
            "is_favorited": False,
            "is_in_shopping_cart": False,
            "name": "Суп",
            "image": "http://testserver/media/image.jpeg",
            "text": "Охапку дров и суп готов.",
            "cooking_time": 20
        }
        url = reverse('recipe-detail', kwargs={'pk': self.recipe.id})
        response = self.client.patch(
            url,
            data=post_data,
            format='json',
            headers=self.headers_authorized_author
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_delete_recipe_unauthorized_user(self):
        """Delete recipe unauthorized user."""
        url = reverse('recipe-detail', kwargs={'pk': self.recipe.id})
        response = self.client.delete(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            'Unauthorized user can not delete recipe.'
        )

    def test_delete_recipe_authorized_user(self):
        """Delete recipe unauthorized user."""
        url = reverse('recipe-detail', kwargs={'pk': self.recipe.id})
        response = self.client.delete(
            url,
            headers=self.headers_authorized
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            'Authorized user can not delete not own recipe.'
        )

    def test_delete_recipe_by_owner(self):
        """Delete recipe by owner."""
        recipe_for_delete = models.Recipe.objects.create(
            author=self.author,
            name='Will delete',
            text='It will be deleted...',
            cooking_time=20,
            image='image.jpeg',
        )
        self.assertTrue(
            models.Recipe.objects.filter(id=recipe_for_delete.id).exists(),
            'Recipe was not created.'
        )

        url = reverse('recipe-detail', kwargs={'pk': recipe_for_delete.id})
        response = self.client.delete(
            url,
            headers=self.headers_authorized_author
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Recipe.objects.filter(id=recipe_for_delete.id).exists(),
            'Recipe was not deleted.'
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipePaginationApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_data = {
            'email': 'test_user@mail.ru',
            'username': 'test_user',
            'first_name': 'test',
            'last_name': 'user',
            'password': make_password('Qwerty123')
        }
        cls.user = User.objects.create(**user_data)
        recipe_objects = [
            models.Recipe(
                author=cls.user,
                name='Картофель отварной.',
                image='image.jpeg',
                text='Возьмите столовую ложку...',
                cooking_time=10
            ) for _ in range(1, 15)
        ]
        models.Recipe.objects.bulk_create(recipe_objects)
        cls.expected_results = [
            {
                "id": i,
                "tags": [],
                "ingredients": [],
                "author": {
                    "id": cls.user.id,
                    "email": cls.user.email,
                    "username": cls.user.username,
                    "first_name": cls.user.first_name,
                    "last_name": cls.user.last_name,
                    "is_subscribed": False
                },
                "name": 'Картофель отварной.',
                "image": "http://testserver/media/image.jpeg",
                "text": "Возьмите столовую ложку...",
                "is_favorited": False,
                "is_in_shopping_cart": False,
                "cooking_time": 10
            } for i in range(1, 15)
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_get_recipe_list_pagination(self):
        """Check pagination when get recipes list."""
        url = reverse('recipe-list')
        response = self.client.get(url)
        self.assertEqual(
            response.data.get('results'),
            self.expected_results[:6]
        )
        self.assertEqual(
            response.data.get('count'),
            14
        )

    def test_get_recipe_list_pagination_with_limit_param(self):
        """Check pagination when get recipes list."""
        limit = 5
        url = reverse('recipe-list')
        url += f'?limit={limit}'
        response = self.client.get(url)
        self.assertEqual(
            response.data.get('results'),
            self.expected_results[:limit]
        )

    def test_get_recipe_list_pagination_with_page_param(self):
        """Check pagination when get recipes list."""
        url = reverse('recipe-list')
        url += '?page=2'
        response = self.client.get(url)
        self.assertEqual(
            response.data.get('results'),
            self.expected_results[6:12]
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipeSearchParamsApiTestCase(APITestCase):
    """Testing of search params."""
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

        cls.author_lunch = User.objects.create(
            email='author_lunch@mail.ru',
            username='author_lunch',
        )
        cls.author_diner = User.objects.create(
            email='author_diner@mail.ru',
            username='author_diner',
        )

        cls.diner_tag = models.Tag.objects.create(
            name='Ужин',
            color='#ffffff',
            slug='diner'
        )
        cls.lunch_tag = models.Tag.objects.create(
            name='Обед',
            color='#ffffff',
            slug='lunch'
        )

        cls.recipe_lunch = models.Recipe.objects.create(
            author=cls.author_lunch,
            name='Супер обед.',
            image='image.jpeg',
            text='Возьмите столовую ложку...',
            cooking_time=60
        )
        cls.recipe_diner = models.Recipe.objects.create(
            author=cls.author_diner,
            name='Супер ужин.',
            image='image.jpeg',
            text='Возьмите столовую ложку...',
            cooking_time=30
        )
        cls.recipe_no_tag = models.Recipe.objects.create(
            author=cls.user,
            name='Без тега.',
            image='image.jpeg',
            text='Возьмите столовую ложку...',
            cooking_time=1
        )
        cls.recipe_lunch.tags.add(cls.lunch_tag)
        cls.recipe_diner.tags.add(cls.diner_tag)

        models.Favorite.objects.create(
            user=cls.user,
            recipe=cls.recipe_lunch
        )
        models.ShoppingCart.objects.create(
            user=cls.user,
            recipe=cls.recipe_lunch
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_is_favorited_search_param(self):
        """Check is_favorited search param."""
        is_favorited = 1
        url = reverse('recipe-list')
        url += f'?is_favorited={is_favorited}'
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertTrue(
            response.data.get('results')[0].get('is_favorited'),
        )
        self.assertEqual(
            len(response.data.get('results')),
            1
        )

    def test_is_in_shopping_cart_search_param(self):
        """Check is_in_shopping_cart search param."""
        is_in_shopping_cart = 1
        url = reverse('recipe-list')
        url += f'?is_in_shopping_cart={is_in_shopping_cart}'
        response = self.client.get(url, headers=self.headers_authorized)
        self.assertTrue(
            response.data.get('results')[0].get('is_in_shopping_cart'),
        )
        self.assertEqual(
            len(response.data.get('results')),
            1
        )

    def test_author_search_param(self):
        """Check author search param."""
        author_id = self.author_lunch.id
        url = reverse('recipe-list')
        url += f'?author={author_id}'
        response = self.client.get(url, headers=self.headers_authorized)
        author = response.data.get('results')[0].get('author')
        self.assertEqual(
            author.get('id'),
            self.author_lunch.id
        )
        self.assertEqual(
            len(response.data.get('results')),
            1
        )

    def test_tag_search_param(self):
        """Check tag in search param."""
        tag_slug = self.diner_tag.slug
        url = reverse('recipe-list')
        url += f'?tags={tag_slug}'
        response = self.client.get(url, headers=self.headers_authorized)
        tag = response.data.get('results')[0].get('tags')[0]
        self.assertEqual(
            tag.get('id'),
            self.diner_tag.id
        )
        self.assertEqual(
            len(response.data.get('results')),
            1
        )

    def test_several_tag_search_params(self):
        """Check several tags in search param."""
        tag_slug_diner = self.diner_tag.slug
        tag_slug_lunch = self.lunch_tag.slug
        url = reverse('recipe-list')
        url += f'?tags={tag_slug_diner}&tags={tag_slug_lunch}'
        response = self.client.get(url, headers=self.headers_authorized)
        expected_tags = [
            self.diner_tag.id,
            self.lunch_tag.id
        ]
        recipes = response.data.get('results')
        for recipe in recipes:
            self.assertIn(
                recipe.get('tags')[0].get('id'),
                expected_tags,
                'Recipe have unexpected tag.'
            )
        self.assertEqual(
            len(response.data.get('results')),
            2,
        )
