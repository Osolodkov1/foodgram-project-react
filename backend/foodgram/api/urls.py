from django.urls import include, path
from rest_framework import routers

from .views import (UsersViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)

router_v1 = routers.DefaultRouter()

router_v1.register(r'users', UsersViewSet, basename='users')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
