################################################################################################
from datetime import timedelta
from unittest.mock import Mock, patch

from celery.exceptions import Retry
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tracker.habit_services import get_burning_habits, reminder, telegram_bot_sendtext
from tracker.models import Habit
from tracker.tasks import burning_habits_reminder_task

User = get_user_model()


class HabitCRUDTests(APITestCase):
    client: APIClient

    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(email="testuser@example.com", password="qwer1234", is_active=True)
        self.authenticate(self.user)

        # Создаем тестовую привычку
        self.habit = Habit.objects.create(
            action="Пробежка",
            location="Парк",
            date_start="2026-01-30T08:00:00Z",
            periodicity_days=1,
            time_to_complete=60,
            owner=self.user,
            is_public=False,
        )

        # URL'ы
        self.create_url = reverse("tracker:habit-create")
        self.detail_url = reverse("tracker:habit-detail", kwargs={"pk": self.habit.pk})
        self.update_url = reverse("tracker:habit-update", kwargs={"pk": self.habit.pk})
        self.delete_url = reverse("tracker:habit-delete", kwargs={"pk": self.habit.pk})
        self.list_url = reverse("tracker:habit-list")

    def authenticate(self, user):
        """Логинит пользователя и устанавливает токен"""
        login_url = reverse("users:login")
        response = self.client.post(login_url, {"email": user.email, "password": "qwer1234"}, format="json")
        # Проверяем, что логин удался
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Login failed for {user.email}")
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def test_create_habit(self):
        """Тест создания новой привычки"""
        data = {
            "action": "Медитация",
            "location": "Дом",
            "date_start": "2026-01-30T07:00:00Z",
            "periodicity_days": 1,
            "time_to_complete": 60,
            "is_pleasant": True,
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 2)
        habit = Habit.objects.last()
        self.assertEqual(habit.owner, self.user)

    def test_retrieve_habit(self):
        """Тест получения привычки по ID (владелец)"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], self.habit.action)

    def test_retrieve_habit_unauthorized(self):
        """Тест получения чужой привычки — запрещено"""
        self.client.logout()
        another_user = User.objects.create_user(email="other@example.com", password="qwer1234", is_active=True)
        self.authenticate(another_user)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_habits_owner_sees_own_and_public(self):
        """Владелец видит свои + публичные привычки"""
        public_habit = Habit.objects.create(
            action="Публичная привычка",
            location="Спортзал",
            date_start="2024-05-01T09:00:00Z",
            periodicity_days=1,
            time_to_complete=60,
            is_public=True,
            owner=User.objects.create_user(email="other@example.com"),
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actions = [item["action"] for item in response.data["results"]]
        self.assertIn(self.habit.action, actions)
        self.assertIn(public_habit.action, actions)

    def test_list_habits_other_user_sees_only_public(self):
        """Другой пользователь видит только публичные привычки"""
        self.client.logout()
        other_user = User.objects.create_user(email="other@example.com", password="qwer1234", is_active=True)
        self.authenticate(other_user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actions = [item["action"] for item in response.data["results"]]
        self.assertNotIn(self.habit.action, actions)  # Своя? Нет!
        # Но если есть публичные — должны быть
        public_habit = Habit.objects.create(
            action="Общая привычка",
            location="Улица",
            date_start="2026-01-30T10:00:00Z",
            periodicity_days=2,
            time_to_complete=60,
            is_public=True,
            owner=self.user,
        )
        response = self.client.get(self.list_url)
        actions = [item["action"] for item in response.data["results"]]
        self.assertIn(public_habit.action, actions)

    def test_update_habit_owner(self):
        """Тест обновления привычки владельцем"""
        data = {"action": "Обновлённая пробежка", "location": "Новый парк"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.action, "Обновлённая пробежка")

    def test_update_habit_not_owner(self):
        """Тест обновления чужой привычки — запрещено"""
        self.client.logout()
        other_user = User.objects.create_user(email="other@example.com", password="qwer1234", is_active=True)
        self.authenticate(other_user)

        data = {"action": "Злоумышленник меняет"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_habit_owner(self):
        """Тест удаления привычки владельцем"""
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Habit.DoesNotExist):
            self.habit.refresh_from_db()

    def test_delete_habit_not_owner(self):
        """Тест удаления чужой привычки — запрещено"""
        self.client.logout()
        other_user = User.objects.create_user(email="other@example.com", password="qwer1234", is_active=True)
        self.authenticate(other_user)

        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.habit.refresh_from_db()
        self.assertTrue(self.habit.is_active)

    def test_create_habit_validation_reward_and_related(self):
        """Нельзя указывать и вознаграждение, и связанную привычку"""
        pleasant_habit = Habit.objects.create(
            action="Йога",
            location="Дом",
            date_start="2026-01-30T08:00:00Z",
            periodicity_days=1,
            time_to_complete=60,
            is_pleasant=True,
            owner=self.user,
        )
        data = {
            "action": "Чтение",
            "location": "Библиотека",
            "date_start": "2026-01-30T19:00:00Z",
            "periodicity_days": 1,
            "time_to_complete": 60,
            "reward": "Чашка чая",
            "related_habit": pleasant_habit.pk,
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Нельзя одновременно указывать вознаграждение и связанную привычку", str(response.data))

    def test_create_pleasant_habit_cannot_have_reward_or_related(self):
        """Приятная привычка не может иметь вознаграждение или связанную привычку"""
        data = {
            "action": "Прослушивание музыки",
            "location": "Дом",
            "date_start": "2026-01-30T20:00:00Z",
            "periodicity_days": 1,
            "time_to_complete": 60,
            "is_pleasant": True,
            "reward": "Наслаждение",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("У приятной привычки не может быть вознаграждения", str(response.data))


class HabitServicesTestCase(TestCase):
    """
    Набор тестов для проверки логики сервисов привычек (habit_services).
    Проверяются:
    - Получение активных привычек, требующих напоминания.
    - Деактивация просроченных привычек.
    - Работа Telegram-напоминаний.
    - Обработка ошибок при отправке сообщений.
    """

    def setUp(self):
        """
        Подготовка мок-объекта привычки перед каждым тестом.
        Создаётся объект с необходимыми атрибутами и мокируется метод __str__.
        """
        self.habit = Mock()
        self.habit.is_active = True
        self.habit.date_start = timezone.now() - timedelta(days=2)
        self.habit.periodicity_days = timedelta(days=1)
        self.habit.last_notified_at = timezone.now() - timedelta(days=2)
        self.habit.__str__ = Mock(return_value="Напоминание: Пить воду — Ежедневно")

    @patch("tracker.habit_services.Habit.objects.filter")
    def test_get_burning_habits_no_active_habits(self, mock_filter):
        """
        Тест: если нет активных привычек, ожидается исключение.
        Проверяет, что get_burning_habits() выбрасывает исключение при пустом списке.
        """
        mock_filter.return_value = []
        with self.assertRaisesRegex(Exception, "Нет активных привычек"):
            get_burning_habits()

    @patch("tracker.habit_services.Habit.objects.filter")
    def test_get_burning_habits_habit_deactivated_if_expired(self, mock_filter):
        """
        Тест: привычка должна быть деактивирована, если срок действия истёк.
        Проверяет, что is_active становится False и вызывается save().
        """
        self.habit.date_end = timedelta(days=1)
        self.habit.date_start = timezone.now() - timedelta(days=3)
        mock_filter.return_value = [self.habit]

        with patch.object(self.habit, "save") as mock_save:
            try:
                habits = get_burning_habits()
                self.assertEqual(len(habits), 0)
                self.assertFalse(self.habit.is_active)
                mock_save.assert_called()
            except Exception:
                self.fail("Exception raised during get_burning_habits()")

    @patch("tracker.habit_services.Habit.objects.filter")
    def test_get_burning_habits_in_burning_list_due_to_next_notification(self, mock_filter):
        """
        Тест: привычка попадает в список «горящих», если пора отправлять уведомление.
        Проверяет, что привычка возвращается при достижении времени следующего уведомления.
        """
        self.habit.date_end = timedelta(days=10)
        mock_filter.return_value = [self.habit]

        habits = get_burning_habits()
        self.assertEqual(len(habits), 1)
        self.assertIs(habits[0], self.habit)

    @patch("tracker.habit_services.Habit.objects.filter")
    def test_get_burning_habits_first_notification_time_reached(self, mock_filter):
        """
        Тест: первое уведомление должно быть отправлено после date_start.
        Проверяет корректность работы при отсутствии last_notified_at.
        """
        self.habit.date_end = timedelta(days=10)
        self.habit.last_notified_at = None
        self.habit.date_start = timezone.now() - timedelta(days=2)
        mock_filter.return_value = [self.habit]

        habits = get_burning_habits()
        self.assertEqual(len(habits), 1)

    @patch("tracker.habit_services.Habit.objects.filter")
    def test_get_burning_habits_too_early_for_notification(self, mock_filter):
        """
        Тест: уведомление не отправляется, если ещё не прошёл периодичный интервал.
        Проверяет, что привычка не попадает в список, если прошло меньше времени, чем periodicity_days.
        """
        self.habit.date_end = timedelta(days=10)
        self.habit.last_notified_at = timezone.now() - timedelta(hours=10)
        self.habit.periodicity_days = timedelta(days=1)
        mock_filter.return_value = [self.habit]

        habits = get_burning_habits()
        self.assertEqual(len(habits), 0)

    @patch("tracker.habit_services.telebot")
    def test_telegram_bot_sendtext_success(self, mock_telebot):
        """
        Тест: успешная отправка сообщения через Telegram-бота.
        Проверяет, что бот инициализируется и отправляет сообщение с правильным текстом.
        """
        bot_instance = Mock()
        mock_telebot.TeleBot.return_value = bot_instance

        from habit_tracker.settings import BOT_TOKEN, CHAT_ID

        telegram_bot_sendtext(self.habit)

        mock_telebot.TeleBot.assert_called_once_with(token=BOT_TOKEN, parse_mode=None)
        bot_instance.send_message.assert_called_once_with(chat_id=CHAT_ID, text=self.habit.__str__())

    @patch("tracker.habit_services.BOT_TOKEN", None)
    def test_telegram_bot_sendtext_missing_token(self):
        """
        Тест: ошибка при отсутствии BOT_TOKEN.
        Проверяет, что функция выбрасывает ValueError, если токен не задан.
        """
        with self.assertRaisesRegex(ValueError, "BOT_TOKEN не загружен!"):
            telegram_bot_sendtext(self.habit)

    @patch("tracker.habit_services.CHAT_ID", None)
    @patch("tracker.habit_services.BOT_TOKEN", "fake_token")
    def test_telegram_bot_sendtext_missing_chat_id(self):
        """
        Тест: ошибка при отсутствии CHAT_ID.
        Проверяет, что функция выбрасывает ValueError, если ID чата не задан.
        """
        with self.assertRaisesRegex(ValueError, "CHAT_ID не загружен!"):
            telegram_bot_sendtext(self.habit)

    @patch("tracker.habit_services.telegram_bot_sendtext")
    def test_reminder_calls_sendtext_for_each_habit(self, mock_sendtext):
        """
        Тест: функция reminder вызывает отправку сообщения для каждой привычки.
        Проверяет, что sendtext вызывается столько раз, сколько привычек передано.
        """
        habit1 = Mock()
        habit2 = Mock()
        reminder([habit1, habit2])
        self.assertEqual(mock_sendtext.call_count, 2)

    @patch("tracker.habit_services.telegram_bot_sendtext", side_effect=Exception("Network error"))
    @patch("tracker.habit_services.logger")
    def test_reminder_handles_exception_gracefully(self, mock_logger, _mock_sendtext):
        """
        Тест: reminder корректно обрабатывает ошибки при отправке.
        Проверяет, что при исключении в sendtext логгер фиксирует ошибку, но выполнение продолжается.
        """
        habit = Mock()
        reminder([habit])
        mock_logger.error.assert_called()


class HabitTasksTestCase(TestCase):
    """Набор тестов для задач из tracker.tasks."""

    @patch("tracker.tasks.get_burning_habits")
    @patch("tracker.tasks.reminder")
    def test_burning_habits_reminder_task_success(self, mock_reminder, mock_get_habits):
        """
        Тестирует успешное выполнение задачи burning_habits_reminder_task.
        Ожидается: получение списка привычек, отправка напоминаний, возврат результата.
        """
        # Подготовка
        mock_habits = [Mock(), Mock()]
        mock_get_habits.return_value = mock_habits
        mock_reminder.return_value = {"status": "OK"}

        # Выполнение
        result = burning_habits_reminder_task()

        # Проверки
        mock_get_habits.assert_called_once()
        mock_reminder.assert_called_once_with(mock_habits)
        self.assertEqual(result, {"status": "OK"})

    @patch("tracker.tasks.get_burning_habits")
    @patch("tracker.tasks.logger")
    def test_burning_habits_reminder_task_no_habits(self, mock_logger, mock_get_habits):
        """
        Тестирует поведение задачи, когда нет активных привычек.
        Ожидается: логирование, возврат сообщения о пустом результате.
        """
        mock_get_habits.return_value = []

        result = burning_habits_reminder_task()

        mock_logger.info.assert_any_call("Нет привычек, требующих напоминаний.")
        self.assertEqual(result, "Нет активных напоминаний.")

    @patch("tracker.tasks.get_burning_habits")
    @patch("tracker.tasks.reminder", side_effect=Exception("Network error"))
    def test_burning_habits_reminder_task_retry_on_exception(self, _mock_reminder, mock_get_habits):
        """
        Тестирует автоматический retry при возникновении исключения в reminder.
        Ожидается: вызов self.retry() с передачей исключения.
        """
        # Подготовка: get_burning_habits возвращает привычки → НЕ должно быть исключения тут
        mock_habits = [Mock()]
        mock_get_habits.return_value = mock_habits  # ✅ Убедитесь, что не выбрасывает исключение!

        # Мокируем атрибуты Celery-задачи
        with (
            patch.object(burning_habits_reminder_task, "max_retries", 3),
            patch.object(burning_habits_reminder_task, "default_retry_delay", 60),
        ):
            retry_mock = Mock(side_effect=Retry)
            with patch.object(burning_habits_reminder_task, "retry", retry_mock):
                with self.assertRaises(Retry):
                    burning_habits_reminder_task()

            retry_mock.assert_called_once()
            kwargs = retry_mock.call_args.kwargs
            self.assertIn("exc", kwargs)
            self.assertEqual(str(kwargs["exc"]), "Network error")


################################################################################################
