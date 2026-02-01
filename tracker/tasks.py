###############################################################################
import logging

from celery import shared_task

from tracker.habit_services import get_burning_habits, reminder

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def burning_habits_reminder_task(self):
    """
    Celery задача для отправки напоминаний по "горящим" привычкам.

    Задача:
        1. Получает список привычек, которым необходимо отправить напоминание.
        2. Отправляет напоминания через сервис `reminder`.
        3. При возникновении временной ошибки — автоматически повторяет попытку (до 3 раз).

    Использует механизм retry из Celery для устойчивости к временным сбоям
    (например, проблемы с сетью, БД или внешними сервисами).

    Returns:
        dict: Результат выполнения в формате {habit_id: status, ...} или сообщение об ошибке.

    Raises:
        Exception: Перехватывается и логируется. Задача может быть повторена.
    """
    try:
        logger.info("Запуск задачи: проверка 'горящих' привычек для напоминаний.")
        burning_habits = get_burning_habits()
        logger.debug(f"Найдено {len(burning_habits)} привычек, требующих напоминания.")

        if not burning_habits:
            logger.info("Нет привычек, требующих напоминаний.")
            return "Нет активных напоминаний."
        # Отправляем напоминания
        result = reminder(burning_habits)
        logger.info("Напоминания успешно обработаны.")
        return result
    except Exception as e:
        logger.exception("Ошибка при выполнении задачи напоминания.")
        # Повторная попытка через 60 секунд (default_retry_delay=60)
        raise self.retry(exc=e)  # exc=e для отслеживания цепочки перезапусков


###############################################################################
