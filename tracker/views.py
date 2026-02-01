###################################################################################
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from tracker.models import Habit
from tracker.serializers import HabitSerializer
from users.paginators import CustomPageNumberPagination


class BaseHabitView:
    """
    Базовый класс для всех операций с привычками.

    Обеспечивает ограничение доступа только авторизованным пользователям
    и фильтрацию queryset'а по владельцу привычки.

    Наследуется всеми представлениями, где требуется проверка принадлежности привычки.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = HabitSerializer

    def get_queryset(self):
        """
        Возвращает привычки, принадлежащие текущему пользователю.

        :return: QuerySet объектов Habit, где owner = request.user
        """
        return Habit.objects.filter(owner=self.request.user)


@extend_schema(
    tags=["Habits"],
    summary="Регистрация новой привычки",
    description="Создает новую привычку для текущего пользователя.",
)
class HabitCreateAPIView(generics.CreateAPIView):
    """
    Представление для создания новой привычки.

    Обрабатывает POST-запросы на создание новой записи модели Habit.
    Привязывает новую привычку к текущему пользователю и активирует её по умолчанию.

    #### Основные возможности:
    - Создание новой привычки.
    - Автоматическое назначение владельца (текущий пользователь).
    - Активация привычки при создании (is_active=True).

    #### Метод HTTP:
    - POST /habits/create/: Создание новой привычки.

    #### Права доступа:
    - Доступно только авторизованным пользователям (IsAuthenticated).

    #### Особенности:
    - Поле `owner` заполняется автоматически.
    - Используется сериализатор HabitSerializer для валидации входных данных.
    """

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """
        Сохраняет новую привычку, устанавливая текущего пользователя как владельца.

        :param serializer: Сериализатор HabitSerializer
        """
        serializer.save(owner=self.request.user, is_active=True)


@extend_schema(
    tags=["Habits"],
    summary="Получение привычки по ID",
    description="Возвращает данные привычки. Доступно владельцу.",
)
class HabitDetailAPIView(BaseHabitView, generics.RetrieveAPIView):
    """
    Представление для получения детальной информации о привычке.

    Возвращает данные привычки по её уникальному идентификатору.
    Доступ разрешён только владельцу привычки.

    #### Основные возможности:
    - Просмотр деталей конкретной привычки.

    #### Метод HTTP:
    - GET /habits/<id>/: Получение информации о привычке.

    #### Права доступа:
    - Доступно только владельцу привычки (через BaseHabitView).

    #### Особенности:
    - Запрос фильтруется по полю owner, поэтому если пользователь не является владельцем,
      будет возвращена ошибка 404.
    """

    pass


@extend_schema(
    tags=["Habits"],
    summary="Редактирование привычки полученной по ID",
    description="Редактирование привычки доступно только владельцу.",
)
class HabitUpdateAPIView(BaseHabitView, generics.UpdateAPIView):
    """
    Представление для обновления существующей привычки.

    Обрабатывает PUT и PATCH запросы для изменения данных привычки.
    Доступ разрешён только владельцу привычки.

    #### Основные возможности:
    - Полное (PUT) или частичное (PATCH) обновление привычки.

    #### Методы HTTP:
    - PUT /habits/<id>/: Полное обновление привычки.
    - PATCH /habits/<id>/: Частичное обновление привычки.

    #### Права доступа:
    - Доступно только владельцу привычки (через BaseHabitView).

    #### Особенности:
    - Все изменения применяются только к привычкам, принадлежащим пользователю.
    """

    pass


@extend_schema(
    tags=["Habits"],
    summary="Удаление привычки полученной по ID",
    description="Удаление привычки доступно только владельцу.",
)
class HabitDeleteAPIView(BaseHabitView, generics.DestroyAPIView):
    """
    Представление для удаления привычки.

    Удаляет привычку по её идентификатору.
    Доступ разрешён только владельцу привычки.

    #### Основные возможности:
    - Удаление привычки из системы.

    #### Метод HTTP:
    - DELETE /habits/<id>/: Удаление привычки.

    #### Права доступа:
    - Доступно только владельцу привычки (через BaseHabitView).

    #### Особенности:
    - Удаление происходит немедленно (без подтверждения на уровне API).
    """

    pass


@extend_schema(
    tags=["Habits"],
    summary="Получение списка привычек",
    description="Получение списка привычек. Доступно только авторизованным пользователям. "
    "Для владельца возвращаются и свои привычки, и публичные привычки. "
    "Для остальных — только публичные",
)
class HabitListAPIView(generics.ListAPIView):
    """
    Представление для получения списка привычек.

    Возвращает список привычек в зависимости от роли пользователя:
    - Владелец видит свои привычки и все публичные.
    - Другие авторизованные пользователи видят только публичные привычки.

    #### Основные возможности:
    - Получение списка привычек с фильтрацией.
    - Поддержка пагинации.

    #### Метод HTTP:
    - GET /habits/: Получение списка привычек.

    #### Права доступа:
    - Доступно только авторизованным пользователям (IsAuthenticated).

    #### Фильтрация:
    Результаты можно фильтровать по следующим полям:
        - `is_public` — публичная/приватная привычка.
        - `is_pleasant` — приятная привычка.
        - `location` — место выполнения.

    #### Пагинация:
    - Включена кастомная пагинация (CustomPageNumberPagination).

    #### Особенности:
    - Используется объединённый QuerySet: свои привычки + публичные.
    - Реализовано через Q-объект: `Q(owner=user) | Q(is_public=True)`
    """

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Возвращает привычки: принадлежащие пользователю или помеченные как публичные.

        :return: QuerySet объектов Habit с фильтрацией по владельцу или публичности
        """
        user = self.request.user
        return Habit.objects.filter(Q(owner=user) | Q(is_public=True))


###################################################################################
