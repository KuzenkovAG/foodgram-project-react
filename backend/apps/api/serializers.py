from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import ValidationError

from ..recipes import models
from . import fields
from .utils import create_ingredients

User = get_user_model()
SUBSCRIPTION_ACTIONS = [
    'get_subscriptions',
    'subscribe'
]


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Short information about recipe."""
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for view User."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
            'is_subscribed', 'recipes', 'recipes_count'
        )
        read_only = ('id', 'is_subscribed', 'recipes_count')
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, author):
        """Check is user follow to author or not."""
        follows = self.context.get('follows')
        return author in follows

    def validate_password(self, value):
        """Make hash from password to save it in DB."""
        return make_password(value)

    def to_representation(self, instance):
        """Remove additions field."""
        self.__remove_field_is_subscribed()
        self.__remove_fields_with_recipes()
        return super().to_representation(instance)

    def __remove_field_is_subscribed(self):
        """Remove field is_subscribed for signup."""
        request = self.context.get('request')
        if request.method == 'POST' and request.path == reverse('user-list'):
            self.fields.pop('is_subscribed')

    def __remove_fields_with_recipes(self):
        """Remove additions field related with Subscription action."""
        action = self.context.get('view').action
        if action not in SUBSCRIPTION_ACTIONS:
            self.fields.pop('recipes', None)
            self.fields.pop('recipes_count', None)


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
        user.password = make_password(new_password)
        user.save()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag."""
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'color', 'slug')

    def to_internal_value(self, data):
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient."""
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.Serializer):
    """Serializer for ingredient."""
    id = serializers.IntegerField()
    name = serializers.CharField(read_only=True)
    measurement_unit = serializers.CharField(read_only=True)
    amount = serializers.IntegerField()

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, amount):
        if int(amount) <= 0:
            raise ValidationError('Amount should be not 0.')
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
    tags = TagSerializer(many=True)
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

    def validate_cooking_time(self, amount):
        if int(amount) <= 0:
            raise ValidationError('Amount should be not 0.')
        return int(amount)

    def validate(self, attrs):
        tags = attrs.get('tags')
        if models.Tag.objects.filter(id__in=tags).count() != len(set(tags)):
            raise ValidationError('Tag object not exists.')
        return attrs

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
        instance.ingredients.set(ingredients)
        instance.tags.set(tags)
        return instance
