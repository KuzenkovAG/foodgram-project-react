from django.contrib.auth import get_user_model
from django.db.models import Count, OuterRef, Prefetch, Subquery
from django.http import HttpResponse
from rest_framework import status

from ..recipes import models

User = get_user_model()


def add_follows_to_context(context, user):
    """Add follows of user to context."""
    result = set()
    if user.is_authenticated:
        follows = user.follows.all()
        for author in follows:
            result.add(author.author)
    context['follows'] = result


def add_shipping_cart_to_context(context, user):
    """Add shopping cart of user to context."""
    result = set()
    if user.is_authenticated:
        shoppings = user.shoppings.all()
        for shipping_cart in shoppings:
            result.add(shipping_cart.recipe)
    context['shoppings'] = result


def add_favorites_to_context(context, user):
    """Add favorites of user to context."""
    result = set()
    if user.is_authenticated:
        favorites = user.favorites.all()
        for favorite in favorites:
            result.add(favorite.recipe)
    context['favorites'] = result


def create_ingredients(ingredients):
    """Create ingredients amount objects for recipe."""
    ingredients_objects = (
        models.IngredientAmount(
            ingredient=models.Ingredient(id=ingredient.get('id')),
            amount=ingredient.get('amount')
        ) for ingredient in ingredients
    )
    return models.IngredientAmount.objects.bulk_create(ingredients_objects)


def get_query_with_recipes_and_recipes_limit(query, recipe_limit):
    """Add field recipes count and limit of recipes."""
    if recipe_limit and recipe_limit.isnumeric():
        recipe_limit = int(recipe_limit)
    else:
        recipe_limit = None
    subquery = Subquery(
        models.Recipe.objects.filter(
            author_id=OuterRef('author_id')
        ).values_list('id', flat=True)[:recipe_limit]
    )
    return query.prefetch_related(Prefetch(
        'recipes', queryset=models.Recipe.objects.filter(id__in=subquery))
    ).annotate(recipes_count=Count("recipes"))


def get_query_with_subscriptions(user, recipe_limit):
    """Get subscriptions of user with limited recipes."""
    query = User.objects.filter(followers__follower=user).order_by('-id')
    return get_query_with_recipes_and_recipes_limit(query, recipe_limit)


def _prepare_ingredients_to_print(ingredients):
    """Prepare ingredients to print."""
    data = []
    for ingredient in ingredients:
        name = ingredient.get('name')
        units = ingredient.get('measurement_unit')
        total = ingredient.get('total')
        row = f'{name} {total}{units}\n'
        data.append(row)
    return ''.join(data)


def get_response_with_attachment(ingredients):
    """Prepare response with attachment."""
    ingredients = _prepare_ingredients_to_print(ingredients)
    response = HttpResponse(
        ingredients,
        content_type='text/plain; charset=UTF-8',
        status=status.HTTP_200_OK
    )
    response['Content-Disposition'] = (
        'attachment; filename=ingredients.txt'
    )
    return response
