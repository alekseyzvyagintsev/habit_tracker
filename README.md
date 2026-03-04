# Habit Tracker

Приложение для отслеживания полезных привычек с напоминаниями через Telegram-бота.

---

## Локальная настройка и запуск

### Предварительные требования

- Docker и Docker Compose
- `.env` файл с переменными окружения (пример ниже)

### 1. Клонирование репозитория

bash git clone https://github.com/alekseyzvyagintsev/habit_tracker.git cd habit_tracker


### 2. Создание `.env` файла

Создайте файл `.env` в корне проекта:

### Общие
- SECRET_KEY=your-secret-key-here
- DEBUG=False
- IN_DOCKER=True

### База данных
- DB_NAME=habit_tracker
- DB_USER=postgres
- DB_PASSWORD=postgres
- DB_HOST=db
- DB_PORT=5432

### Redis
- REDIS_HOST=redis://redis:6379/0

### Email (пример)
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=your@gmail.com
- EMAIL_HOST_PASSWORD=yourpassword
- DEFAULT_FROM_EMAIL=your@gmail.com

### Другие
- BOT_TOKEN=your_telegram_bot_token
- CHAT_ID=your_chat_id
- STRIPE_KEY=your_stripe_key


> Все чувствительные данные (особенно пароли и ключи) должны быть защищены. В продакшене используйте `DEBUG=False`.

### 3. Запуск приложения через Docker

bash docker-compose up --build


После запуска:
- Django доступен по адресу: `http://localhost:8000`
- Админка: `http://localhost/admin/`
- Статика и медиа автоматически обслуживаются через Nginx
- Celery и Celery Beat работают в фоне

> Первый запуск может занять больше времени из-за сборки образов и миграций.

---

## CI/CD и деплой на сервер

Проект использует GitHub Actions для непрерывной интеграции и доставки.

### Архитектура CI/CD

1. **Build** — сборка Docker-образа и публикация в Docker Hub.
2. **Deploy** — автоматический деплой на удалённый сервер при пуше или pull request (в `main`/`master` опционально).

### Настройка секретов в GitHub

> Перейдите в `Settings > Secrets and variables > Actions` и добавьте:

| Имя                                            | Описание                                                        |
|------------------------------------------------|-----------------------------------------------------------------|
| `DOCKERHUB_USERNAME`                           | Ваш логин в Docker Hub                                          |
| `DOCKERHUB_TOKEN`                              | Токен доступа к Docker Hub                                      |
| `SERVER_IP`                                    | IP-адрес сервера (например, VPS)                                |
| `SERVER_USER`                                  | Пользователь на сервере (например, `root`)                      |
| `DEPLOY_DIR`                                   | Путь на сервере для деплоя (например, `/var/www/habit_tracker`) |
| `SSH_KEY`                                      | Приватный SSH-ключ (с правами на запись в репозиторий и сервер) |
| `SECRET_KEY`, `BOT_TOKEN`, `DB_PASSWORD` и др. | Переменные окружения для продакшена                             |

### Процесс деплоя

1. После пуша или pull request (в `main` опционально):
   - Запускается workflow `ci.yml`.
   - Образ собирается и отправляется в Docker Hub.
   - Выполняется деплой на сервер.

2. На сервере:
   - Копируются `docker-compose.yml` и `nginx.conf`.
   - Создаётся `.env` с продакшен-переменными.
   - Останавливается старая версия (`docker compose down`).
   - Подтягивается новый образ (`docker compose pull`).
   - Запускается новая версия (`docker compose up -d`).

> При необходимости можно включить условие для деплоя только в `main`:  
> в ci.yml: jobs: deploy:
> -    if: github.ref == 'refs/heads/main'

---

## Структура проекта
    habit_tracker/ 
    ├── .github/
    │   └── workflows/
    │      └──ci.yml # CI/CD пайплайн 
    ├── nginx/
    │   └──nginx.conf # Конфиг Nginx 
    ├── collected_static/ # Собранные статические файлы 
    ├── static/
    ├── config/
    │   └── redis.conf
    ├── habit_tracker/
    │   ├── settings.py
    │   ├── urls.py
    │   └── ... 
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    ├── .env
    ├── tracker # Приложение контролирующее привычки
    ├── users/ # Приложение для регистрации и управления пользователями
    └── ...

---

# !!! ВАЖНО !!!
### При поднятии проекта создается база данных,
### для доступа к ней создается 3 пользователя:
- admin@example.com
- moderator@example.com
- user@example.com
### с одинаковыми паролями 'qwer1234'
# !!!! ОБЯЗАТЕЛЬНО СМЕНИТЕ ПАРОЛИ !!!!

# !!! Также важно !!!
### Для правильной работы прав доступа, при создании новых пользователей,
### чтобы они были активированы и входили в соответствующие для них группы.
- 'Администратор'
- 'Модератор'
- 'Пользователь'

## Запуск приложения

### 1. Сборка и запуск: bash
- docker compose up --build # Сборка и запуск
- docker compose up -d # Запуск в фоновом режиме
- Приложение будет доступно по адресу: `http://localhost` или `http://127.0.0.1` или `http://0.0.0.0` - IP-адрес сервера

### 2. Остановка и очистка: bash
- docker-compose down -v # Остановка и очистка предыдущих контейнеров и томов
- docker compose down -v --remove-orphans # Остановка и очистка неиспользуемых контейнеров
- docker system prune -a # Очистка всех контейнеров, образов и томов !!!! Необратимо для восстановления.
- docker volume prune # Очистка томов
- docker compose down # Остановка

### 3. Проверка: bash
- docker compose logs -f # Просмотр логов
- docker compose ps # Список запущенных сервисов

---

## Архитектура сервисов (`docker-compose.yml`)

| Сервис   | Назначение                         |
|----------|------------------------------------|
| `db`     | PostgreSQL 16.0, хранение данных   |
| `redis`  | Хранилище для Celery и кэширования |
| `web`    | Django-сервер (`runserver`)        |
| `celery` | Воркер для фоновых задач           |
| `beat`   | Планировщик периодических задач    |

---

## Поддержка

Разработчик: Алексей  
Email: alex0236889@yandex.ru  
