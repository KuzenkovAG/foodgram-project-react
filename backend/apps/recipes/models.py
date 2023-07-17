from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Tags for recipes."""
    name = models.CharField(max_length=32)
    color = models.CharField(max_length=7)
    slug = models.CharField(max_length=64)


class Ingredient(models.Model):
    """Ingredients for recipes."""
    name = models.CharField(max_length=64)
    measurement_unit = models.CharField(max_length=16)


class IngredientAmount(models.Model):
    """Amount of ingredients."""
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.SmallIntegerField()


class Recipe(models.Model):
    """Model of recipe."""
    name = models.CharField(max_length=200)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    text = models.TextField()
    image = models.ImageField(upload_to='recipes/')
    cooking_time = models.SmallIntegerField()
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(IngredientAmount)


class Favorite(models.Model):
    """Favorites recipes of user."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite'
    )


class ShoppingCart(models.Model):
    """Cart with recipes for purchasing of user."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppings',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_cart'
    )


class Follow(models.Model):
    """Follow of other users."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Автор',
    )
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows',
        verbose_name='Подписчик',
    )
