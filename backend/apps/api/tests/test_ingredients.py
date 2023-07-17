from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ...recipes import models

User = get_user_model()


class IngredientApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ingredient_data = {
            'name': 'Капуста',
            'measurement_unit': 'кг'
        }
        cls.ingredient = models.Ingredient.objects.create(**ingredient_data)

    def test_get_ingredients_list(self):
        """Get list of ingredients."""
        url = reverse('ingredient-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                'id': self.ingredient.id,
                'name': 'Капуста',
                'measurement_unit': 'кг'
            }
        ]
        self.assertEqual(response.data, expected_data)

    def test_get_ingredient_by_id(self):
        """Get ingredient by id."""
        url = reverse('ingredient-detail', kwargs={'pk': self.ingredient.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            'id': self.ingredient.id,
            'name': 'Капуста',
            'measurement_unit': 'кг'
        }
        self.assertEqual(response.data, expected_data)

    def test_get_not_existing_ingredient(self):
        """Get not existing ingredient."""
        url = reverse('ingredient-detail', kwargs={'pk': 12})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_ingredients(self):
        """Search ingredients."""
        url = reverse('ingredient-list')
        search_frase = 'пуста'
        url += '?search=' + search_frase
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                'id': self.ingredient.id,
                'name': 'Капуста',
                'measurement_unit': 'кг'
            }
        ]
        self.assertEqual(response.data, expected_data)
