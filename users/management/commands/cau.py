#############################################################################################################
import logging

from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

from users.models import User

logger = logging.getLogger(__name__)


def create_admin_group():
    admin_group, created = Group.objects.get_or_create(name="Администратор")
    if created:
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        logger.info("Группа 'Администратор' создана и назначены все права.")
    else:
        logger.info("Группа 'Администратор' уже существует.")


def create_moderator_group():
    moderator_group, created = Group.objects.get_or_create(name="Модератор")
    if created:
        logger.info("Группа 'Модератор' создана.")
    else:
        logger.info("Группа 'Модератор' уже существует.")


def create_user_group():
    user_group, created = Group.objects.get_or_create(name="Пользователь")
    if created:
        logger.info("Группа 'Пользователь' создана.")
    else:
        logger.info("Группа 'Пользователь' уже существует.")


class Command(BaseCommand):
    help = "Создаёт суперпользователя, модератора и тестового пользователя."

    def handle(self, *args, **options):
        create_admin_group()
        create_moderator_group()
        create_user_group()

        # Создание админа
        admin, created = User.objects.get_or_create(
            email="admin@example.com", defaults={"is_staff": True, "is_superuser": True}
        )
        if created:
            admin.set_password("qwer1234")
            admin.is_active = True
            admin.save()
            admin_group = Group.objects.get(name="Администратор")
            admin.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS(f"Суперпользователь {admin.email} создан."))
        else:
            self.stdout.write(f"Пользователь {admin.email} уже существует.")

        # Создание модератора
        moderator, created = User.objects.get_or_create(email="moderator@example.com", defaults={"is_staff": True})
        if created:
            moderator.set_password("qwer1234")
            moderator.is_active = True
            moderator.save()
            moderator_group = Group.objects.get(name="Модератор")
            moderator.groups.add(moderator_group)
            self.stdout.write(self.style.SUCCESS(f"Модератор {moderator.email} создан."))
        else:
            self.stdout.write(f"Модератор {moderator.email} уже существует.")

        # Создание пользователя
        user, created = User.objects.get_or_create(email="user@example.com")
        if created:
            user.set_password("qwer1234")
            user.is_active = True
            user.save()
            user_group = Group.objects.get(name="Пользователь")
            user.groups.add(user_group)
            self.stdout.write(self.style.SUCCESS(f"Пользователь {user.email} создан."))
        else:
            self.stdout.write(f"Пользователь {user.email} уже существует.")


#############################################################################################################
