from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=200,
        unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=100
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Тег',
        max_length=200,
        unique=True
    )
    slug = models.SlugField(unique=True)
    color = ColorField(
        verbose_name='Цвет в HEX',
        default='#FF0000',
        unique=True
    )

    class Meta:
        ordering = ['-name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'slug', 'color'],
                name='unique_tag'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200
    )
    image = models.ImageField(
        verbose_name='Фото',
        upload_to='recipes/',
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='Ингредиент',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipe',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        default=0,
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_recipe',
            ),
        )

    def __str__(self):
        return f'{self.name}'


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент в рецепте',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиентов в рецепте',
        default=0,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ['ingredient']
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient',),
                name='unique_ingredient_in_recipe',
            ),
        )

    def __str__(self):
        return f'{self.ingredient.name}'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed',
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата подписки',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription')]

    def __str__(self):
        return f'{self.author}'


class FavoriteRecipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_favorited',
        verbose_name='Автор избранного',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_favorited',
        verbose_name='Избранный рецепт',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_favorite')
        ]

    def __str__(self):
        recipe = [item['name'] for item in self.recipe.values('name')]
        return f'{recipe}'


class ShoppingCart(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
        verbose_name='Владелец списка покупок',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
        verbose_name='Рецепт в списке покупок',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_shopping_cart',
            ),
        )

    def __str__(self):
        recipe = [item['name'] for item in self.recipe.values('name')]
        return f'{recipe}'
