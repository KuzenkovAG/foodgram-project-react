from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Tags for recipes."""
    name = models.CharField(max_length=32)
    color = models.CharField(max_length=7)
    slug = models.CharField(max_length=64)

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    """Ingredients for recipes."""
    name = models.CharField(max_length=64)
    measurement_unit = models.CharField(max_length=16)

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class IngredientAmount(models.Model):
    """Amount of ingredients."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amounts'
    )
    amount = models.SmallIntegerField()

    def __str__(self):
        return (
            f'{self.ingredient.name} '
            f'{self.amount}{self.ingredient.measurement_unit}'
        )


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
    ingredients = models.ManyToManyField(
        IngredientAmount,
        related_name='in_recipes'
    )

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

    def get_count_in_favorites(self):
        return self.in_favorite.count()


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_in_cart'
            )
        ]


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'follower'],
                name='unique_author_follower'
            )
        ]
