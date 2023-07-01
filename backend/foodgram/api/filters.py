from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag
from rest_framework.filters import SearchFilter


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    author = filters.CharFilter(
        field_name='author__id',
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(is_favorited__author=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(is_in_shopping_cart__author=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited')
