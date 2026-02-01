##############################################################################################
from django.db import models
from django.utils import timezone

from tracker.habit_validators import validate_habit_fields
from users.models import User


class Habit(models.Model):
    """
    Модель привычки.

    Описывает действие, которое пользователь хочет формировать,
    включая параметры выполнения: время, место, периодичность, награду,
    а также связи с другими привычками и настройки видимости.

    Поля:
        action (str): Основное действие привычки (например, «пробежка», «медитация»).
        date (datetime): Дата и время создания записи. Устанавливается автоматически.
        location (str): Место выполнения привычки (например, «парк», «спальня»).
        owner (User): Пользователь, которому принадлежит привычка. Может быть null.
        related_habit (Habit): Связанная привычка. Должна быть приятной, если используется.
        periodicity_days (int): Интервал выполнения в днях (1 — ежедневно, 7 — раз в неделю реже нельзя).
        reward (str): Текстовое вознаграждение за выполнение (например, «выпить кофе»).
        time_to_complete (timedelta): Максимальное время на выполнение привычки (до 2 минут по умолчанию).
        is_pleasant (bool): Является ли привычка приятной (не требует вознаграждения и может быть связана с другими).
        is_public (bool): Доступна ли привычка для просмотра другим пользователям.
        is_active (bool): Активна ли привычка (используется для мягкого удаления).

    Валидация:
        Перед сохранением вызывается `clean()`, который использует `validate_habit_fields` —
        проверяет логические ограничения:
          - У приятной привычки не может быть вознаграждения или связанной привычки.
          - Связанная привычка должна быть приятной.
          - Нельзя одновременно указать вознаграждение и связанную привычку.
          - Время выполнения не должно превышать 120 секунд.
          - Периодичность — от 1 до 7 дней.

    Методы:
        clean(): Выполняет валидацию через отдельную функцию.
        save(): Автоматически вызывает clean() перед сохранением.

    Мета:
        ordering: Сортировка по дате создания.
        verbose_name: Человекочитаемое имя модели.
        verbose_name_plural: Число множественное.

    Пример строки (str):
        'user@example.com планирует бег в 2024-05-01 10:00:00 в парке. Привязана к None'
    """

    action = models.CharField(max_length=200, verbose_name="Действие")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    last_notified_at = models.DateTimeField(null=True, blank=True, verbose_name="Время последнего оповещения")
    date_start = models.DateTimeField(default=timezone.now, verbose_name="Дата и время начала")
    date_end = models.DurationField(default=timezone.timedelta(days=30), verbose_name="Период действия")
    location = models.CharField(max_length=200, verbose_name="Место")
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="habits",  # user.habits.all()
        verbose_name="Владелец",
    )
    related_habit = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="linked_habits",  # habit.linked_habits.all()
        verbose_name="Связанная привычка",
    )
    # Число дней между выполнением привычки.
    # Например: 1 → каждый день; 7 → раз в неделю; (30 → раз в месяц - запрещено условием валидации)
    periodicity_days = models.DurationField(default=timezone.timedelta(days=1), verbose_name="Периодичность (дни)")
    reward = models.CharField(max_length=200, null=True, blank=True, verbose_name="Вознаграждение")
    time_to_complete = models.DurationField(
        default=timezone.timedelta(seconds=120), verbose_name="Время на выполнение"
    )
    is_pleasant = models.BooleanField(default=False, verbose_name="Приятная привычка")
    is_public = models.BooleanField(default=False, verbose_name="Публичная")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        reward = self.reward or (self.related_habit.action if self.related_habit else "нет вознаграждения)))")
        return f"Пришло время закрепить привычку: '{self.action}', " f"а за тем у Вас {reward}."

    def __repr__(self):
        related_habit = self.related_habit.action if self.related_habit else "нет данных"
        reward = self.reward or "нет данных"
        return (
            f"{self.owner.email} планирует {self.action} c {self.date_start} по {self.date_start + self.date_end} "
            f"в {self.location} один раз в {self.periodicity_days} дней. "
            f"Связана с: {related_habit} или вознаграждение: {reward}"
        )

    def clean(self):
        # Преобразование времени на выполнение в секундах
        if self.time_to_complete is not None:
            if isinstance(self.time_to_complete, int):
                self.time_to_complete = timezone.timedelta(seconds=self.time_to_complete)
            elif isinstance(self.time_to_complete, float):
                self.time_to_complete = timezone.timedelta(seconds=int(self.time_to_complete))

        # Преобразование Периодичности повторения в днях
        if self.periodicity_days is not None:
            if isinstance(self.periodicity_days, int):
                self.periodicity_days = timezone.timedelta(days=self.periodicity_days)
            elif isinstance(self.periodicity_days, float):
                self.periodicity_days = timezone.timedelta(days=int(self.periodicity_days))

        # Преобразование Периода действия в днях
        if self.date_end is not None:
            if isinstance(self.date_end, int):
                self.date_end = timezone.timedelta(days=self.date_end)
            elif isinstance(self.date_end, float):
                self.date_end = timezone.timedelta(days=int(self.date_end))

        # Выполняет валидацию модели перед сохранением.
        validate_habit_fields(self)

    def save(self, *args, **kwargs):
        # Переопределение метода save для вызова валидации перед сохранением.
        if not self.date_start:
            self.date_start = self.created_at
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("date_start",)
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"


##############################################################################################
