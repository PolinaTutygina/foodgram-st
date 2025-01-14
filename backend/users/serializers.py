from rest_framework import serializers
from django.contrib.auth import get_user_model
from recipes.serializers import RecipeSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'avatar', 'is_subscribed'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.subscribers.filter(id=request.user.id).exists()


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']


class PasswordResetSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен быть не менее 8 символов.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'avatar', 'recipes', 'recipes_count'
        ]

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeSerializer(recipes, many=True).data


class SubscribeActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id']

    def validate_id(self, value):
        user = self.context['request'].user
        if value == user.id:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        if user.subscriptions.filter(id=value).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        target_user = User.objects.get(id=self.validated_data['id'])
        user.subscriptions.add(target_user)
        return target_user
