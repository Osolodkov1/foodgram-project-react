from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            ShoppingCart, Subscribe, Tag, IngredientInRecipe)
from users.models import User
from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import (IngredientSerializer, RecipeCreateSerializer,
                             RecipeReadSerializer, SubscribeSerializer,
                             TagSerializer, ShortRecipeSerializer)
from api.generate_pdf_file import generate_pdf_file


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='subscribe',
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def subscribe(self, request, **kwargs):
        user = get_object_or_404(User, id=kwargs.get('id'))
        subscribe = Subscribe.objects.filter(user=request.user, author=user)
        if request.method == 'POST':
            if user == request.user:
                msg = {'error': 'Нельзя подписаться на самого себя.'}
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            obj, created = Subscribe.objects.get_or_create(
                user=request.user,
                author=user
            )
            if not created:
                msg = {'error': 'Вы уже подписаны на этого пользователя.'}
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscribeSerializer(obj, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not subscribe.exists():
            msg = {'error': 'Вы не подписаны на этого пользователя.'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def subscriptions(self, request):
        subscribe = Subscribe.objects.filter(user=request.user)
        pages = self.paginate_queryset(subscribe)
        serializer = SubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filterset_class = RecipeFilter
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH', 'PUT']:
            return RecipeCreateSerializer
        return RecipeReadSerializer

    def add_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        models = model.objects.filter(author=request.user, recipe=recipe)
        if models.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model(author=request.user, recipe=recipe).save()
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def del_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        models = model.objects.filter(author=request.user, recipe=recipe)
        if models.exists():
            models.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='favorite',
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def favorite(self, request, **kwargs):
        if request.method == 'POST':
            return self.add_recipe(FavoriteRecipe, request, kwargs.get('pk'))
        return self.del_recipe(FavoriteRecipe, request, kwargs.get('pk'))

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def shopping_cart(self, request, **kwargs):
        if request.method == 'POST':
            return self.add_recipe(ShoppingCart, request, kwargs.get('pk'))
        return self.del_recipe(ShoppingCart, request, kwargs.get('pk'))

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        get_cart = IngredientInRecipe.objects.filter(
            recipe__is_in_shopping_cart__author=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(Sum('amount'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment;'
        text_cart = ''
        for value in get_cart:
            text_cart += (
                value['ingredient__name'] + ' - '
                + str(value['amount__sum']) + ' '
                + value['ingredient__measurement_unit'] + '<br/>'
            )
        return generate_pdf_file(text_cart, response)
