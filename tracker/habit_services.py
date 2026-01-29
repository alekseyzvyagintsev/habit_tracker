###############################################################################
import logging

import telebot
from django.utils import timezone

from habit_tracker.settings import BOT_TOKEN, CHAT_ID
from tracker.models import Habit

logger = logging.getLogger(__name__)


def get_burning_habits():
    """
    Возвращает список "горящих" привычек — тех, которым пора отправить напоминание.

    Проходит по всем активным привычкам, проверяет:
     - Не истекла ли дата окончания привычки (если да — деактивирует).
     - Наступило ли время следующего напоминания (на основе periodicity_days).

    Returns:
        List[Habit]: Список привычек, требующих уведомления.

    Raises:
        Exception: Если нет активных привычек.
    """
    now = timezone.now()
    habits_is_active = Habit.objects.filter(is_active=True)
    burning_habits = []

    if not habits_is_active:
        logger.info("Нет активных привычек")
        raise Exception("Нет активных привычек")

    logger.info(f"Найдено {len(habits_is_active)} активных привычек.")

    for habit in habits_is_active:
        # Определяем дату окончания активности привычки
        habit_end_time = habit.date_start + habit.date_end
        # Если привычка уже завершилась — деактивируем
        if now > habit_end_time:
            habit.is_active = False
            habit.save()
            logger.info(f"Привычка '{habit}' деактивирована — срок действия истёк.")
            continue

        if habit.last_notified_at:
            # Получаем дату следующего уведомления
            next_notification = habit.last_notified_at + habit.periodicity_days
            if now >= next_notification:
                burning_habits.append(habit)
        else:
            # Если уведомления еще не было, проверяем, наступило ли время напоминания.
            first_notification = habit.date_start + habit.periodicity_days
            if now >= first_notification:
                burning_habits.append(habit)

    logger.info(f"Найдено {len(burning_habits)} горящих привычек для отправки напоминаний.")
    return burning_habits


def telegram_bot_sendtext(habit):
    """
    Отправляет текстовое сообщение через Telegram-бота.

    Args:
        habit (Habit): Объект привычки, который будет отправлен в сообщении.

    Raises:
        ValueError: Если BOT_TOKEN или CHAT_ID не заданы.
        Exception: При ошибках отправки сообщения.
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не загружен! Проверьте .env и settings.py")
        raise ValueError("BOT_TOKEN не загружен! Проверьте .env и settings.py")
    if not CHAT_ID:
        logger.error("CHAT_ID не загружен! Проверьте .env и settings.py")
        raise ValueError("CHAT_ID не загружен! Проверьте .env и settings.py")

    try:
        # экземпляр класса TeleBot
        bot = telebot.TeleBot(token=BOT_TOKEN, parse_mode=None)
        # отправляем сообщение
        text = f"{habit.__str__()}"
        bot.send_message(chat_id=CHAT_ID, text=text)
        logger.info(f"Уведомление отправлено для привычки: {habit}")
    except Exception:
        logger.exception(f"Критическая ошибка при отправке сообщения в Telegram для привычки {habit}")
        raise


def reminder(burning_habits):
    """
    Отправляет напоминания для списка "горящих" привычек.

    Args:
        burning_habits (List[Habit]): Список привычек, которым нужно отправить уведомление.
    """
    good_sendings = 0
    bad_sendings = 0
    logger.info(f"Получено горящих привычек для напоминания: {len(burning_habits)}")
    for habit in burning_habits:
        try:
            # Отправляем уведомление
            telegram_bot_sendtext(habit)
            # Обновляем время последнего уведомления
            habit.last_notified_at = timezone.now()
            habit.save(update_fields=["last_notified_at"])
            good_sendings += 1
            logger.debug(f"Время последнего уведомления обновлено для привычки: id {habit.id} — {habit.action}")
        except Exception:
            bad_sendings += 1
            logger.error(
                f"Не удалось отправить напоминание для привычки: id {habit.id} — {habit.action}",
                exc_info=True,  # чтобы включить traceback
            )
            logger.info(f"Отправлено напоминаний: {good_sendings}, не удалось отправить: {bad_sendings}")
    return f"Успешно отправлено {good_sendings} напоминаний, не удалось отправить {bad_sendings} напоминаний."


###############################################################################
