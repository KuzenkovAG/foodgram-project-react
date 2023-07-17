from django_filters import FilterSet
from django_filters import rest_framework as filters


class RecipeFilterSet(FilterSet):
    """Recipe filter set."""
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    author = filters.CharFilter(field_name='author')
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shipping_cart')

    def filter_favorited(self, queryset, name, favorite):
        user = self.request.user
        if favorite:
            return queryset.filter(in_favorite__user=user)
        return queryset.exclude(in_favorite__user=user)

    def filter_shipping_cart(self, queryset, name, shipping_cart):
        user = self.request.user
        if shipping_cart:
            return queryset.filter(in_cart__user=user)
        return queryset.exclude(in_cart__user=user)
