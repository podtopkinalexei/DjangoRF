FROM python:3.13.7

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    gdal-bin \
    libgdal-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий для статики и медиа
RUN mkdir -p /app/static /app/media

# Создание пользователя для безопасности
RUN useradd -m -r django && \
    chown -R django:django /app
USER django

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]