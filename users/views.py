#############################################################################################################
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.paginators import CustomPageNumberPagination
from users.models import User
from users.permissions import IsAdminUser, IsUserOwner
from users.serializer import PrivateUserSerializer, PublicUserSerializer


@extend_schema(tags=["Users"])
@extend_schema_view(
    retrieve=extend_schema(
        summary="Детальная информация о пользователе",
    ),
    list=extend_schema(
        summary="Получение списка пользователей.",
    ),
    update=extend_schema(
        summary="Полное (PUT) обновление пользователя.",
    ),
    partial_update=extend_schema(
        summary="Частичное (PATCH) обновление пользователя.",
    ),
    destroy=extend_schema(
        summary="Удаление пользователя.",
    ),
)
class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    ViewSet для работы с моделями пользователей.

    Обеспечивает базовые операции CRUD над пользователями, включая создание нового пользователя,
    получение общего списка пользователей,
    детализацию конкретного пользователя, обновление и удаление.

    #### Основные возможности:
    - Просмотр списка пользователей (ограничено правами доступа).
    - Детальная информация о каждом пользователей (ограничено правами доступа).
    - Редактирование сведений о пользователях (ограничено правами доступа).
    - Возможность удалить пользователя (ограничено правами доступа).

    #### Методы HTTP:
    - GET /users/: Получение списка пользователей.
    - GET /users/id/: Информация о конкретном пользователе.
    - PUT /users/id/: Полное обновление пользователя.
    - PATCH /users/id/: Частичное обновление пользователя.
    - DELETE /users/id/: Удаление пользователя.

    Доступ к различным действиям контролируется системой разрешений:
    - `create`: разрешено анонимному пользователю (AllowAny).
    - `list`: ограничено администратором системы (IsAuthenticated & IsAdminUser).
    - `retrieve`, `update`, `partial_update` и `destroy`: доступ предоставляется либо владельцу аккаунта,
      либо сотруднику с ролью администратора (IsAuthenticated & (IsUserOwner | IsAdminUser)).

    Для сериализации используется два типа сериалайзера:
    - `PrivateUserSerializer`: для приватных данных самого пользователя.
    - `PublicUserSerializer`: для публичного отображения чужих профилей.

    Примечания:
    - Обычные пользователи видят только собственные профили.
    - Администратор видит полный список всех пользователей.
    - Анонимные пользователи имеют право только создать новый аккаунт.
    - Для метода retrieve применен декоратор extend_schema. В данном случае он добавляет схему для сериализатора
    PrivateUserSerializer так-как выбор сериализатора зависит от прав пользователя, то данный сериализатор не виден
    по умолчанию для swagger UI
    """

    queryset = User.objects.all()  # Выборка всех пользователей
    pagination_class = CustomPageNumberPagination  # Кастомный постраничный пагинатор

    def get_permissions(self):
        # Описание прав для каждого варианта запроса
        if self.action == "create":
            self.permission_classes = [
                AllowAny,
            ]  # Создание профиля доступно любому пользователю
        elif self.action == "list":  # Ограничиваем просмотр списка только администраторами
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action == "retrieve":  # Детализированный просмотр пользователя
            self.permission_classes = [IsAuthenticated, IsUserOwner | IsAdminUser]
        elif self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = [IsAuthenticated, IsUserOwner | IsAdminUser]
        return super().get_permissions()

    def get_serializer_class(self):
        # Определим сериализатор на основе текущего пользователя и запрашиваемого объекта
        user = getattr(self.request, "user", None)
        requested_user_id = self.kwargs.get("pk")

        # Если пользователь авторизован и запрашивает собственный профиль
        if user and str(user.id) == requested_user_id:
            return PrivateUserSerializer
        # Если пользователь не авторизован или запрашивает чужой профиль
        return PublicUserSerializer

    def get_queryset(self):
        # Определяем queryset в зависимости от роли пользователя
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return User.objects.all()  # Все пользователи доступны сотрудникам
            return User.objects.filter(id=self.request.user.id)  # Только собственный профиль
        return []

    def list(self, request, *args, **kwargs):
        # Метод запроса списка пользователей
        if not request.user.is_staff:
            raise PermissionDenied("У Вас недостаточно прав для просмотра списка пользователей")
        return super().list(request, *args, **kwargs)

    @extend_schema(responses={200: PrivateUserSerializer})
    def retrieve(self, request, *args, **kwargs):
        # Переопределен метод просмотра подробностей модели пользователя
        instance = self.get_object()  # Получаем объект пользователя по указанному pk
        current_user = request.user  # Текущий авторизованный пользователь

        # Проверяем права доступа
        if current_user.is_superuser or current_user == instance:
            return super().retrieve(request, *args, **kwargs)
        else:
            raise PermissionDenied("У вас недостаточно прав для просмотра профиля.")

    def update(self, request, *args, **kwargs):
        # Метод PUT остается не низменным.
        pass

    def partial_update(self, request, *args, **kwargs):
        # Метод PATCH остается не низменным
        pass

    def destroy(self, request, *args, **kwargs):
        # Метод DELETE остается не низменным
        pass


class UserCreateAPIView(CreateAPIView):
    """
    Представление для создания нового пользователя.

    Метод POST используется для добавления новой записи пользователя.
    Полностью обрабатывается созданием экземпляра объекта User.

    #### Возможности:
    - Только создание нового пользователя.

    #### Метод HTTP:
    - POST /register/: Отправка формы для создания пользователя.
    """

    # Сериализатор для обработки входящей информации
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Регистрация нового пользователя",
        description="Создает нового пользователя с указанным именем, почтой и паролем.",
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


#############################################################################################################
