##############################################################################################
from django.core.management import BaseCommand
from django.db import connection

from tracker.models import Habit
from users.models import User

# Список полезных привычек
HEALTHY_HABIT_LIST = [
    "Выпить стакан воды сразу после пробуждения",
    "Быстро помыть посуду утром или вечером",
    "Проветрить комнату перед сном",
    "Заправить постель",
    "Проверить календарь на ближайшие события",
    "Медитация или дыхательные упражнения",
    "Упражнения для глаз",
    "Написать благодарность кому-нибудь",
    "Расслабляющий массаж шеи и плеч",
    "Обязательно улыбнуться своему отражению в зеркале",
]

# Список приятных привычек
PLEASANT_HABIT_LIST = [
    "Послушать любимую песню",
    "Взглянуть в окно и насладиться видом природы",
    "Попить ароматного чая или кофе",
    "Почитать пару страниц любимой книги",
    "Поделиться улыбкой или комплиментом с кем-то",
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.get(id=1)

        # Удаляем старые привычки, чтобы избежать дубликатов (опционально)
        Habit.objects.filter(owner=user).delete()
        # Сброс последовательности для поля id модели Habit
        with connection.cursor() as cursor:
            cursor.execute("ALTER SEQUENCE tracker_habit_id_seq RESTART WITH 1;")

        # Создание приятных привычек
        for pleasant_habit in PLEASANT_HABIT_LIST:
            Habit.objects.create(
                action=pleasant_habit,
                location="везде",
                owner=user,
                phone_number="+79818108912",
                periodicity_days=1,
                is_pleasant=True,
                is_public=True,
                is_active=True,
            )

        # Получаем приятные привычки в порядке возрастания ID
        pleasant_habits = Habit.objects.filter(owner=user, is_pleasant=True).order_by("id")
        pleasant_count = pleasant_habits.count()

        # Создание приятных привычек
        counter = 1
        for healthy_habit in HEALTHY_HABIT_LIST:
            habit = Habit.objects.create(
                action=healthy_habit,
                location="везде",
                owner=user,
                phone_number="+79818108912",
                periodicity_days=1,
                time_to_complete=60,
                is_pleasant=False,
                is_public=False,
                is_active=True,
            )

            # Привязываем приятную привычку или указываем награду за выполнение
            if counter <= pleasant_count:
                habit.related_habit = pleasant_habits.get(pk=counter)
                counter += 1
            else:
                habit.reward = "капучинка с печенюшкой"

            habit.save()


##############################################################################################
