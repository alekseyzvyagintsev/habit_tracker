#########################################################################################
import logging
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone
from email_validator import EmailNotValidError, validate_email

from habit_tracker import settings
from users.models import User

logger = logging.getLogger(__name__)


def send_email_to_recipient(subject, message, recipient_email):
    """
    Отправляет письмо одному получателю на нормализованный и валидный email-адрес.
    Использует `email_validator` для более строгой валидации и нормализации.
    """
    # Проверяем валидность email
    if not recipient_email:
        logger.error("Пустой email получателя")
        return False

    try:
        # Используем email_validator для валидации и нормализации
        validation_result = validate_email(recipient_email)
        normalized_email = validation_result.normalized
    except EmailNotValidError as e:
        logger.error(f"Некорректный email получателя: {str(e)}")
        return False

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[normalized_email],
            fail_silently=False,
        )
        logger.info(f"Письмо успешно отправлено: {normalized_email}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки письма на {normalized_email}: {str(e)}")
        return False


def send_email_to_recipients(subject, message, recipient_emails):
    """
    Отправляет письмо списку email-адресов.
    Возвращает количество успешно отправленных писем.
    """
    success_count = 0
    for email in recipient_emails:
        if send_email_to_recipient(subject, message, email):
            success_count += 1
    return success_count


def deactivate_expired_users():
    """
    Деактивирует пользователей:
    - которые не заходили более 30 дней,-
    - или никогда не входили, но зарегистрированы более 30 дней назад.
    """
    expiry_time = timezone.now() - timedelta(days=30)
    # Пользователи, которые входили, но давно
    expired_active_users = User.objects.filter(is_active=True, last_login__lt=expiry_time)
    # Пользователи, которые никогда не входили, но зарегистрированы давно
    dormant_expired_users = User.objects.filter(is_active=True, last_login__isnull=True, date_joined__lt=expiry_time)
    # Объединяем QuerySets
    expired_users = expired_active_users.union(dormant_expired_users)
    # Логируем общее количество найденных пользователей
    count = expired_users.count()
    if count == 0:
        logger.info("Нет пользователей, подлежащих деактивации.")
    else:
        logger.info(f"Найдено {count} пользователей для деактивации.")
    # Деактивируем по одному с логированием
    deactivated_count = 0
    for user in expired_users:
        user.is_active = False
        user.save(update_fields=["is_active"])
        logger.info(
            f"Пользователь {user.id} ({user.email}) деактивирован: "
            f"last_login={user.last_login}, date_joined={user.date_joined}"
        )
        deactivated_count += 1

    return deactivated_count


#########################################################################################
