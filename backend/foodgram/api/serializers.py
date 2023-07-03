from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Ingredient, IngredientInRecipe, Recipe, Subscribe,
                            Tag)
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return user.subscriber.filter(author=obj).exists()


class NewAccoutUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        label='Электронная почта',
        required=True
    )
    password = serializers.CharField(
        label='Пароль',
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password',
        )

    def validate_email(self, data):
        if User.objects.filter(email=data).exists():
            raise serializers.ValidationError(
                "Пользователь с такой эл. почтой уже есть."
            )
        return data

    def validate_username(self, data):
        if User.objects.filter(username=data).exists():
            raise serializers.ValidationError(
                "Пользователь с таким юзернеймом уже есть."
            )
        return data

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = IngredientSerializer()
    name = serializers.CharField(
        required=False
    )
    measurement_unit = serializers.IntegerField(
        required=False
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_representation(self, instance):
        data = IngredientSerializer(instance.ingredient).data
        data['amount'] = instance.amount
        return data


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        many=False,
        read_only=True
    )
    tags = TagSerializer(
        many=True
    )
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'name', 'author', 'ingredients', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart',
        )

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return recipe.is_favorited.filter(author=user).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return recipe.is_in_shopping_cart.filter(author=user).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer(
        many=False,
        read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'author',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        tags = self.data.get('tags')
        ingredients = self.data.get('ingredients')
        name = self.data.get('recipe')
        cooking_time = self.data.get('cooking_time')
        if not tags:
            raise serializers.ValidationError('Добавьте хотя бы один тег')
        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент должен быть уникальным!'
                )
            ingredient_list.append(ingredient_id)
            try:
                int(ingredient['amount'])
            except ValueError:
                raise serializers.ValidationError(
                    'Кол-во ингредиентов должно быть указано только цифрами.'
                )
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Укажите количество ингредиентов'
                )
        if len(name) < 3:
            raise serializers.ValidationError(
                'Название рецепта должно содержать не менее 3 символов.'
            )
        name = name[0].upper() + name[1:]
        recipe = Recipe.objects.filter(
            author=self.context['request'].user,
            name=name
        ).exists()
        if recipe and self.context['request'].method == 'POST':
            raise serializers.ValidationError(
                'Вы уже сохранили рецепт с таким названием.'
            )
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время приготовления не должно быть меньше 1 минуты.'
            )
        return data

    def create_ingredients(self, ingredients, recipe):
        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient=Ingredient.objects.get(id=ingredient['id'])
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        ingredients = self.initial_data.get('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        recipe.ingredients.clear()
        recipe.tags.clear()
        ingredients = self.initial_data.get('ingredients')
        tags = validated_data.pop('tags')
        recipe.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        self.create_ingredients(ingredients, recipe)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        data = RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data
        return data


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(UserSerializer):
    id = serializers.ReadOnlyField(
        source='author.id'
    )
    username = serializers.ReadOnlyField(
        source='author.username'
    )
    first_name = serializers.ReadOnlyField(
        source='author.first_name'
    )
    last_name = serializers.ReadOnlyField(
        source='author.last_name'
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes',
        )

    def validate(self, attrs):
        user = self.data.get('user')
        author = self.data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'На самого себя нельзя подписаться'
            )
        subscribed = Subscribe.objects.filter(user=user, author=author)
        if self.initial_data.get('method') == 'POST':
            if subscribed.exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого автора'
                )
        else:
            if not subscribed.exists():
                raise serializers.ValidationError(
                    'Вы не подписаны на этого автора'
                )
        return attrs

    def get_is_subscribed(self, username):
        return True

    def get_recipes(self, data):
        limit = self.context.get('request').query_params.get('recipes_limit')
        if not limit:
            limit = 3
        recipes = data.author.recipe.all()[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data
