from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from users.tasks import deactivate_expired_users_task

# Получаем действующую модель пользователя Django в данном проекте (users.models.User)
User = get_user_model()


class UserAPITests(APITestCase):
    client: APIClient

    def setUp(self):
        admin_group, created = Group.objects.get_or_create(name="Администратор")
        # Создаем пользователей для тестов
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="qwer1234", is_superuser=True, is_staff=True, is_active=True
        )
        self.admin_user.groups.add(admin_group)

        self.regular_user = User.objects.create_user(email="user@example.com", password="qwer1234", is_active=True)
        self.other_user = User.objects.create_user(email="other@example.com", password="qwer1234", is_active=True)

        # URL'ы
        self.user_detail_url = lambda pk: reverse("users:users-detail", kwargs={"pk": pk})

    def authenticate(self, user):
        """Логинит пользователя и устанавливает токен"""
        login_url = reverse("users:login")
        response = self.client.post(login_url, {"email": user.email, "password": "qwer1234"}, format="json")
        # Проверяем, что логин удался
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Login failed for {user.email}")
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    # TEST: Регистрация нового пользователя (POST /register/)
    def test_create_user(self):
        data = {"email": "newuser@example.com", "password": "qwer1234"}
        response = self.client.post("/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)  # 3 из setUp + 1
        self.assertEqual(User.objects.get(email="newuser@example.com").is_active, True)

    # TEST: Получение списка пользователей (GET /users/) — доступно только для админа
    def test_list_users_as_admin(self):
        self.authenticate(self.admin_user)
        url = reverse("users:users-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)  # Все три пользователя

    def test_list_users_as_regular_user(self):
        self.authenticate(self.regular_user)
        url = reverse("users:users-list")
        response = self.client.get(url)
        print(response)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_unauthenticated(self):
        url = reverse("users:users-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TEST: Детали пользователя (GET /users/{id}/)
    def test_retrieve_own_profile(self):
        self.authenticate(self.regular_user)
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.regular_user.email)

    def test_retrieve_other_profile_as_regular_user(self):
        self.authenticate(self.regular_user)
        url = reverse("users:users-detail", kwargs={"pk": self.other_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_any_profile_as_admin(self):
        self.authenticate(self.admin_user)
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.regular_user.email)

    def test_retrieve_profile_unauthenticated(self):
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TEST: Обновление пользователя (PUT/PATCH /users/{id}/)
    def test_update_own_profile(self):
        self.authenticate(self.regular_user)
        data = {"first_name": "Updated Name"}
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, "Updated Name")

    def test_update_other_profile_as_regular_user(self):
        self.authenticate(self.regular_user)
        data = {"first_name": "Hacked!"}
        url = reverse("users:users-detail", kwargs={"pk": self.other_user.id})
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_profile_as_admin(self):
        self.authenticate(self.admin_user)
        data = {"email": "changed@example.com"}
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.email, "changed@example.com")

    # TEST: Удаление пользователя (DELETE /users/{id}/)
    def test_delete_own_profile_not_allowed(self):
        self.authenticate(self.regular_user)
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_profile_as_admin(self):
        self.authenticate(self.admin_user)
        url = reverse("users:users-detail", kwargs={"pk": self.regular_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

    def test_delete_profile_unauthenticated(self):
        response = self.client.delete(self.user_detail_url(self.regular_user.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UsersTasksTestCase(TestCase):
    """Набор тестов для задач из users.tasks."""

    @patch("users.tasks.deactivate_expired_users")
    def test_deactivate_expired_users_task_success(self, mock_deactivate):
        """
        Тестирует успешное выполнение задачи деактивации пользователей.
        Ожидается: вызов сервиса, возврат количества деактивированных.
        """
        mock_deactivate.return_value = 5

        result = deactivate_expired_users_task()

        mock_deactivate.assert_called_once()
        self.assertEqual(result, "Деактивировано пользователей: 5")

    @patch("users.tasks.deactivate_expired_users", side_effect=Exception("DB error"))
    @patch("users.tasks.logger")
    def test_deactivate_expired_users_task_handles_error(self, mock_logger, mock_deactivate):
        """
        Тестирует обработку ошибок в задаче деактивации.
        Ожидается: логирование ошибки, возврат сообщения об ошибке.
        """
        result = deactivate_expired_users_task()

        mock_logger.error.assert_called()
        self.assertIn("Ошибка:", result)
        self.assertIn("DB error", result)


###############################################################################
