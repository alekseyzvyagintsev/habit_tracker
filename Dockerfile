FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимностей
RUN apt-get update && \
    apt-get install -y \
        gcc \
        libpq-dev \
        postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry==2.3.1

# Копируем и устанавливаем зависимости
COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction --no-ansi

# Копируем код
COPY . .

EXPOSE 8000
