from django.contrib.auth import get_user_model
from django.db.models import Count, OuterRef, Prefetch, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilterSet
from .paginators import PageLimitPaginator
from .permisstions import AuthorOrReadOnly
from ..recipes import models
from . import serializers, utils

User = get_user_model()
ERRORS = {
    'recipe_in_favorite': {
        'errors': 'Recipe already in favorite.'
    },
    'recipe_not_in_favorite': {
        'errors': 'Recipe not in favorite.'
    },
    'user_subscribed': {
        'errors': 'User already in subscribed.'
    },
    'user_not_subscribed': {
        'errors': 'User not subscribed.'
    },
    'subscribe_on_yourself': {
        'errors': 'You can not subscribed on yourself.'
    }
}


class UserViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """View set for User."""
    queryset = User.objects.all().order_by('id')
    permission_classes = [IsAuthenticated]
    pagination_class = PageLimitPaginator
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        if (self.action == 'list') or (self.action == 'create'):
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        context = super().get_serializer_context()
        utils.add_follows_to_context(context, self.request.user)
        return context

    def get_queryset(self):
        if self.action == 'get_subscriptions':
            recipe_limit = self.request.query_params.get('recipes_limit')
            query = utils.get_query_with_subscriptions(
                user=self.request.user,
                recipe_limit=recipe_limit,
            )
            return query
        return self.queryset

    @action(methods=['get'], detail=False, url_path='me', url_name='me')
    def get_current_user(self, request):
        """Show information about current user."""
        user = get_object_or_404(User, username=request.user.username)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='set_password')
    def change_password(self, request):
        """Change password of user."""
        serializer = serializers.PasswordSerializer(
            data=request.data,
            instance=self.request.user
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                'Password changed.',
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False, url_path='subscriptions')
    def get_subscriptions(self, request):
        """Get users what following user."""
        users = self.get_queryset()
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe')
    def subscribe(self, request, pk):
        """Subscribe to users."""
        recipe_limit = self.request.query_params.get('recipes_limit')
        user = self.request.user
        author = get_object_or_404(
            utils.get_query_with_recipes_and_recipes_limit(
                User.objects,
                recipe_limit
            ),
            id=pk
        )
        subscription = models.Follow.objects.filter(
            follower=user,
            author=author
        )
        if request.method == 'POST':
            if user == author:
                errors = ERRORS.get('subscribe_on_yourself')
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            if subscription.exists():
                errors = ERRORS.get('user_subscribed')
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            models.Follow.objects.create(follower=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not subscription.exists():
                errors = ERRORS.get('user_not_subscribed')
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TagsViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """ViewSet for tags."""
    queryset = models.Tag.objects.all()
    permission_classes = []
    serializer_class = serializers.TagSerializer
    pagination_class = None


class IngredientViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """ViewSet for ingredients."""
    queryset = models.Ingredient.objects.all()
    permission_classes = []
    serializer_class = serializers.IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for recipes."""
    queryset = models.Recipe.objects.all().order_by('id')
    permission_classes = [AuthorOrReadOnly]
    serializer_class = serializers.RecipeSerializer
    pagination_class = PageLimitPaginator
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        context = super().get_serializer_context()
        user = self.request.user
        utils.add_follows_to_context(context, user)
        utils.add_shipping_cart_to_context(context, user)
        utils.add_favorites_to_context(context, user)
        return context

    @action(methods=['post', 'delete'], detail=True, url_path='favorite')
    def manage_favorites(self, request, pk):
        """Add or remove recipe to favorite."""
        user = self.request.user
        recipe = get_object_or_404(models.Recipe, id=pk)
        favorite = models.Favorite.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if favorite.exists():
                errors = ERRORS.get('recipe_in_favorite')
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            models.Favorite.objects.create(user=user, recipe=recipe)
            serializer = serializers.ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not favorite.exists():
                errors = ERRORS.get('recipe_not_in_favorite')
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
