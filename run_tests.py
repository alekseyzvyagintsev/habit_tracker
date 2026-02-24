# run_tests.py
import os
import django
from django.conf import settings
from django.test.runner import DiscoverRunner
import sys


def run_tests():
    # Устанавливаем переменную окружения для Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "habit_tracker.settings")

    # Инициализируем Django
    django.setup()

    # Запускаем тесты через Django Test Runner
    test_runner = DiscoverRunner(verbosity=2, failfast=False)
    failures = test_runner.run_tests(['users', 'tracker'])

    # Возвращаем код ошибки, если тесты провалились
    sys.exit(bool(failures))


if __name__ == "__main__":
    run_tests()