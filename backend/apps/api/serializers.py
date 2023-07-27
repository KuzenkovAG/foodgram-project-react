from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.validators import ValidationError

from ..recipes import models
from . import fields
from .utils import create_ingredients

User = get_user_model()
MAX_POSITIVE_VALUE = 32767


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Short information about recipe."""
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for User creation."""
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )
        read_only = ('id',)
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(serializers.ModelSerializer):
    """Serializer for view User."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )
        read_only = ('id', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, author):
        """Check is user follow to author or not."""
        follows = self.context.get('follows')
        return author in follows


class UserSubscribeSerializer(serializers.ModelSerializer):
    """Serializer for User subscribes"""
    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, author):
        """Check is user follow to author or not."""
        follows = self.context.get('follows')
        return author in follows


class PasswordSerializer(serializers.Serializer):
    """Serializer for change password."""
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    class Meta:
        fields = ('new_password', 'current_password',)
        read_only = ('new_password', 'current_password')

    def validate_current_password(self, value):
        user = self._kwargs.get('instance')
        if not check_password(value, user.password):
            raise ValidationError('Password is not correct.')
        return value

    def save(self, **kwargs):
        user = self.instance
        new_password = self.validated_data.get('new_password')
        user.set_password(new_password)
        user.save()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag."""
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only = ('name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient."""
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.Serializer):
    """Serializer for ingredient amount."""
    id = serializers.IntegerField()
    name = serializers.CharField(read_only=True)
    measurement_unit = serializers.CharField(read_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = models.IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, amount):
        if int(amount) <= 0:
            raise ValidationError('Amount should more 0.')
        elif int(amount) > MAX_POSITIVE_VALUE:
            raise ValidationError(
                f'Amount should be less {MAX_POSITIVE_VALUE}.'
            )
        return int(amount)

    def to_representation(self, instance):
        obj = {
            'id': instance.ingredient_id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount
        }
        return super().to_representation(obj)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for ingredient."""
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = fields.Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, recipe):
        """Show recipe in favorite or not."""
        favorites = self.context.get('favorites')
        return recipe in favorites

    def get_is_in_shopping_cart(self, recipe):
        """Show recipe in shopping cart or not."""
        shoppings = self.context.get('shoppings')
        return recipe in shoppings

    def validate_ingredients(self, ingredients):
        if len(ingredients) == 0:
            raise ValidationError('Ingredients should be not empty.')
        ingredients_id = [
            ingredient.get('id') for ingredient in ingredients
        ]
        existed_ingredients = models.Ingredient.objects.filter(
            id__in=ingredients_id)
        if len(existed_ingredients) != len(set(ingredients_id)):
            raise ValidationError('Ingredient not found.')
        return ingredients

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result['tags'] = TagSerializer(instance.tags, many=True).data
        return result

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        validated_data['author'] = self.context.get('request').user
        recipe = models.Recipe.objects.create(**validated_data)
        ingredients = create_ingredients(ingredients_data)
        recipe.ingredients.set(ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        ingredients = create_ingredients(ingredients_data)
        instance.ingredients.clear()
        instance.ingredients.set(ingredients)
        instance.tags.set(tags)
        return instance
