from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    """Tags for recipes."""
    name = models.CharField(max_length=32)
    color = models.CharField(max_length=7)
    slug = models.CharField(max_length=64)


# class RecipeTag(models.Model):
#     recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
#     tag = models.ForeignKey('Tag', on_delete=models.CASCADE)


class Ingredient(models.Model):
    """Ingredients for recipes."""
    name = models.CharField(max_length=64)
    measurement_unit = models.CharField(max_length=16)


class RecipeIngredient(models.Model):
    """Many-to-many relations of Recipes and Ingredients."""
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.SmallIntegerField()


class Recipe(models.Model):
    """Model of recipe."""
    name = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    image = models.ImageField()
    cocking_time = models.SmallIntegerField()
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(Ingredient, through=RecipeIngredient)


class Favorite(models.Model):
    """Favorites recipes of user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recept = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class ShoppingCart(models.Model):
    """Cart with recipes for purchasing of user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class Follow(models.Model):
    """Follow of other users."""
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    follower = models.ForeignKey(User, on_delete=models.CASCADE)
