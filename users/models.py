#############################################################################################
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Расширенная модель пользователя.

    Эта модель расширяет стандартную модель пользователя Django (AbstractUser), добавляя дополнительные поля
    для хранения контактной информации, аватара и токенов активации аккаунта.

    Поля:
        * email (EmailField): Уникальная почта пользователя (используется как основное имя пользователя).
        * phone_number (CharField): Номер телефона пользователя (необязательно).
        * avatar (ImageField): Изображение профиля пользователя (необязательно).
        * country (CharField): Страна проживания пользователя (необязательно).
        * is_active (BooleanField): Активирован ли аккаунт пользователя (по умолчанию неактивен).
        * activation_token (CharField): Токен подтверждения регистрации (необязательно).
        * token_expires_at (DateTimeField): Срок истечения токена подтверждения регистрации (необязательно).

    Методы:
        * __str__(): Возвращает электронную почту пользователя в качестве строкового представления.

    Конфигурация:
        * USERNAME_FIELD (str): Поле, используемое для идентификации пользователя (почта).
        * REQUIRED_FIELDS (list): Список обязательных полей помимо username и password.
        * verbose_name (str): Название одной записи в единственном числе.
        * verbose_name_plural (str): Название множества записей.
        * ordering (list): Порядок сортировки объектов.
        * db_table (str): Название таблицы в БД.
    """

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
    ]

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = [
            "username",
        ]
        db_table = "user"


#############################################################################################
