##############################################################################################################
from rest_framework import serializers

from users.models import User


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор для модели User.

    **Обязательные поля для регистрации:**
    - `email`: Существующий адрес электронной почты пользователя. Используется при подтверждении.
    - `username`: уникальное имя пользователя
    - `password`: Пароль хешируется при создании пользователя.

    **Настройки:**
    - `model`: Используется модель User.
    - `fields`: Только "id", "email" и "username".
    - 'extra_kwargs': Параметр write_only=True определяет, что поле предназначено исключительно
      для ввода данных при создании или обновлении ресурса (операций типа POST или PATCH)
    - `read_only_fields`: ID автоматически генерируется системой и доступен только для чтения.

    **Методы**
    - 'Create': Используется для создания пользователя с применением обязательных полей.
    """

    class Meta:
        model = User
        fields = ["id", "email", "username", "password"]
        read_only_fields = ("id",)
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=True,
        )
        return user


class PrivateUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.

    **Обязательные поля для регистрации:**
    - `email`: Существующий адрес электронной почты пользователя. Используется при подтверждении.
    - `password`: Пароль хешируется при создании пользователя.

    **Настройки:**
    - `model`: Используется модель User.
    - `fields`: Все поля модели.
    - 'extra_kwargs': Параметр write_only=True определяет, что поле предназначено исключительно
      для ввода данных при создании или обновлении ресурса (операций типа POST или PATCH)
    - `read_only_fields`: ID автоматически генерируется системой и доступен только для чтения.
    """

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ("id",)


##############################################################################################################
