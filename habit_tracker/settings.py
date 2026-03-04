############################################################################################
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv(override=True)

# Настройки проекта и пути
BASE_DIR = Path(__file__).resolve().parent.parent

# Ключ для шифрования
SECRET_KEY = os.getenv("SECRET_KEY")

# Токен телеграмм бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Режим отладки
DEBUG = True if os.getenv("DEBUG") == "True" else False

# Домены, которые будут использоваться
ALLOWED_HOSTS = ["*"]

# Флаг: работаем ли в Docker?
IN_DOCKER = os.getenv("IN_DOCKER", "False").lower() in ("true", "1", "on", "yes")

# Приложения Django
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "django_celery_beat",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
    "django.contrib.admindocs",
    "users",
    "tracker",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

# Точка входа в приложение для URL-адресов
ROOT_URLCONF = "habit_tracker.urls"

# Шаблоны проекта
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
            ],
        },
    },
]

WSGI_APPLICATION = "habit_tracker.wsgi.application"

# База данных
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "uni_school"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost" if not IN_DOCKER else "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    },
}

# Password validation
# Использование встроенных проверок безопасности
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Требуется для аутентификации пользователей.
# Использование альтернативных моделей пользователей (например, своя реализация User-модели).
# Добавление дополнительных проверок безопасности (например, двухфакторная аутентификация).
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "users.User"  # модель пользователя

LANGUAGE_CODE = "ru-RU"  # язык

TIME_ZONE = "Europe/Moscow"  # временная зона

USE_I18N = True  # позволит отображать страницы сайта на нужном языке

USE_TZ = True  # сохраняет временные метки в базе данных в UTC и автоматически конвертирует их в локальное

# URL-путь, используемый браузером для обращения к статическим ресурсам
STATIC_URL = "static/"

# Относительный путь для сбора статических файлов
STATIC_ROOT = BASE_DIR / "collected_static"
# Исходный путь для хранения статики в приложении
STATICFILES_DIRS = (BASE_DIR / "static",)
# Автоинкремент полей
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URL-путь для медиа-файлов
MEDIA_URL = "media/"
# Относительный путь для хранения медиа-файлов
MEDIA_ROOT = BASE_DIR / "media"

# Настройки API и CORS для Django REST Framework и CORS заголовков для Django и React
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Настройки почты
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = True if os.getenv("EMAIL_USE_TLS") == "True" else False
EMAIL_USE_SSL = True if os.getenv("EMAIL_USE_SSL") == "True" else False
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

# Настройки кэша
CACHE_ENABLED = True
if IN_DOCKER:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://redis:6379/1",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://localhost:6379/1",
        }
    }

#
APSCHEDULER_DATETIME_FORMAT = "d-m-Y H:i:s"
SCHEDULER_DEFAULT = True

# Настройки логирования
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tracker": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Настройки Spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "habit-tracker API",
    "DESCRIPTION": "Test description",
    "VERSION": "v1",
    "TERMS_OF_SERVICE": "https://www.google.com/policies/terms/",
    "CONTACT": {"email": "contact@snippets.local"},
    "LICENSE": {"name": "BSD License"},
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_GENERATION_SETTINGS": {
        "EXCLUDE_PROTECTED_APIS": False,  # Включаем защищённые маршруты в документацию
    },
}

# Настройки разрешений CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",  # адрес бэкенд-сервера
]
# Разрешения для CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://read-only.example.com",  # адрес фронтенд-сервера
    "http://localhost:8000",  # адрес бэкенд-сервера
]
# Разрешение для всех доменов
CORS_ALLOW_ALL_ORIGINS = False

# Настройки Celery и Redis для асинхронных задач и очереди

if IN_DOCKER:
    # URL-адрес брокера сообщений
    CELERY_BROKER_URL = "redis://redis:6379/0"
    # URL-адрес брокера результатов
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"
else:
    # URL-адрес брокера сообщений
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    # URL-адрес брокера результатов, также Redis
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Настройки сериализации для Celery
CELERY_ACCEPT_CONTENT = ["json"]
# Формат сериализации
CELERY_TASK_SERIALIZER = "json"
# Формат сериализации результатов
CELERY_RESULT_SERIALIZER = "json"

# Временная зона для Celery
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "Europe/Moscow"
# Флаг отслеживания выполнения задач
CELERY_TASK_TRACK_STARTED = True
# Максимальное время на выполнение задачи
CELERY_TASK_TIME_LIMIT = 30 * 60
# Расписание для периодических задач
if SCHEDULER_DEFAULT:
    CELERY_BEAT_SCHEDULE = {
        "deactivate_expired_users_task": {
            "task": "users.tasks.deactivate_expired_users_task",
            "schedule": timedelta(minutes=1),
        },
        "burning_habits_reminder_task": {
            "task": "tracker.tasks.burning_habits_reminder_task",
            "schedule": timedelta(minutes=1),
        },
    }

# В конце файла
if not DEBUG:
    print("STATIC_ROOT:", STATIC_ROOT)
    print("STATICFILES_DIRS:", STATICFILES_DIRS)
    print("STATIC_URL:", STATIC_URL)


############################################################################################
