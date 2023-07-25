from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ...recipes import models
from .utils import delete_tags

User = get_user_model()


class TagsApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tag_data = {
            'name': 'tag_name',
            'color': '#000000',
            'slug': 'breakfast'
        }
        cls.tag = models.Tag.objects.create(**tag_data)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        delete_tags()

    def test_get_tag_list(self):
        """Get tags list."""
        url = reverse('tag-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                'id': self.tag.id,
                'name': 'tag_name',
                'color': '#000000',
                'slug': 'breakfast'
            }
        ]
        self.assertEqual(response.data, expected_data)

    def test_get_tag_retrieve(self):
        """Get tag by id."""
        url = reverse('tag-detail', kwargs={'pk': self.tag.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            'id': self.tag.id,
            'name': 'tag_name',
            'color': '#000000',
            'slug': 'breakfast'
        }
        self.assertEqual(response.data, expected_data)

    def test_get_tag_retrieve_404(self):
        """Tag is absent in db."""
        url = reverse('tag-detail', kwargs={'pk': 12})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
