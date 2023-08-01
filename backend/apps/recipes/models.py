from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()
MAX_POSITIVE_VALUE = 32767
MIN_VALUE = 1


class Tag(models.Model):
    """Tags for recipes."""
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название'
    )
    color = models.CharField(max_length=7, unique=True, verbose_name='Цвет')
    slug = models.CharField(max_length=64, unique=True, verbose_name='Slug')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    """Ingredients for recipes."""
    name = models.CharField(max_length=64, verbose_name='Называние')
    measurement_unit = models.CharField(
        max_length=16,
        verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class IngredientAmount(models.Model):
    """Amount of ingredients."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amounts',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(MAX_POSITIVE_VALUE)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return (
            f'{self.ingredient.name} '
            f'{self.amount}{self.ingredient.measurement_unit}'
        )


class Recipe(models.Model):
    """Model of recipe."""
    name = models.CharField(max_length=200, verbose_name='Название')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='recipes/', verbose_name='Изображение')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(MAX_POSITIVE_VALUE),
            MinValueValidator(MIN_VALUE)
        ],
        verbose_name='Время приготовления'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    ingredients = models.ManyToManyField(
        IngredientAmount,
        related_name='in_recipes',
        verbose_name='Ингредиенты'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def get_count_in_favorites(self):
        return self.in_favorite.count()


class Favorite(models.Model):
    """Favorites recipes of user."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
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
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
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
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'follower'],
                name='unique_author_follower'
            ),
            models.CheckConstraint(
                name="prevent_self_follow",
                check=~models.Q(author=models.F("follower")),
            ),
        ]
