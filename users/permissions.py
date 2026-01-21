from rest_framework import permissions

from users.models import User


class IsAdminUser(permissions.BasePermission):
    """
    Разрешает доступ только пользователям с правами администратора.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name="Администратор").exists()


class IsModer(permissions.BasePermission):
    """
    Разрешает доступ только пользователям входящих в группу модераторов.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name="Модератор").exists()


class IsUserOwner(permissions.BasePermission):
    """
    Редактирование и удаление модели доступно только владельцу.
    """

    def has_object_permission(self, request, view, obj):
        # Запись доступна только владельцу объекта
        if isinstance(obj, User):
            # Доступ к аккаунту
            return obj == request.user
        else:
            # Доступ к другим моделям
            return obj.owner == request.user
