from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..recipes import models
from . import serializers, utils
from .filters import RecipeFilterSet
from .paginators import PageLimitPaginator
from .permissions import AuthorOrReadOnly
from .responses import get_response_for_create_or_delete

User = get_user_model()


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

    def get_serializer_class(self):
        if self.action in ['subscribe', 'get_subscriptions']:
            return serializers.UserSubscribeSerializer
        elif self.action == 'change_password':
            return serializers.PasswordSerializer
        elif self.request.method == 'POST':
            return serializers.UserCreateSerializer
        return serializers.UserSerializer

    def get_queryset(self):
        if self.action == 'get_subscriptions':
            recipe_limit = self.request.query_params.get('recipes_limit')
            query = utils.get_query_with_subscriptions(
                user=self.request.user,
                recipe_limit=recipe_limit,
            )
            return query
        return self.queryset

    def perform_create(self, serializer):
        password = serializer.validated_data.get('password')
        serializer.validated_data['password'] = make_password(password)
        serializer.save()

    @action(methods=['get'], detail=False, url_path='me', url_name='me')
    def get_current_user(self, request):
        """Show information about current user."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='set_password')
    def change_password(self, request):
        """Change password of user."""
        serializer = self.get_serializer(
            data=request.data,
            instance=self.request.user
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('Password changed.', status=status.HTTP_201_CREATED)

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
        if user == author:
            errors = 'You can not subscribed on yourself.'
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        response = get_response_for_create_or_delete(
            method=request.method,
            obj=author,
            relation_model=models.Follow,
            action=self.action,
            data={
                'follower': user,
                'author': author
            },
            serializer_class=self.get_serializer
        )
        return response


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
        recipe = get_object_or_404(models.Recipe, id=pk)
        response = get_response_for_create_or_delete(
            method=request.method,
            obj=recipe,
            relation_model=models.Favorite,
            action=self.action,
            data={
                'user': self.request.user,
                'recipe': recipe
            },
            serializer_class=serializers.ShortRecipeSerializer
        )
        return response

    @action(methods=['get'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Download list of ingredients from shopping cart."""
        user = self.request.user
        ingredients = models.Ingredient.objects.filter(
            amounts__in_recipes__in_cart__user=user
        ).values(
            'name',
            'measurement_unit',
        ).annotate(total=Sum('amounts__amount')).order_by('-total')
        return utils.get_response_with_attachment(ingredients)

    @action(methods=['post', 'delete'], detail=True, url_path='shopping_cart')
    def manage_shopping_cart(self, request, pk):
        """Add or delete recipes in shopping cart."""
        recipe = get_object_or_404(models.Recipe, id=pk)
        response = get_response_for_create_or_delete(
            method=request.method,
            obj=recipe,
            relation_model=models.ShoppingCart,
            action=self.action,
            data={
                'user': self.request.user,
                'recipe': recipe
            },
            serializer_class=serializers.ShortRecipeSerializer
        )
        return response
