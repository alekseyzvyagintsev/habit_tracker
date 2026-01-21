###############################################################################
import logging

from celery import shared_task

from users.services import deactivate_expired_users

logger = logging.getLogger(__name__)


@shared_task
def deactivate_expired_users_task():
    """Celery задача для деактивации неактивных пользователей."""
    try:
        count = deactivate_expired_users()
        return f"Деактивировано пользователей: {count}"
    except Exception as e:
        logger.error(e)
        return f"Ошибка: {str(e)}"


###############################################################################
