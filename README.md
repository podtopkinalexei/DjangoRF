## Учебный проект SkyPro "Decker"

### Предварительные требования

- Docker
- Docker Compose

### Запуск проекта

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd DjangoRF
   ```

2. **Настройте переменные окружения**
   ```bash
   cp .env   
   ```

3. **Запустите проект**
   ```bash
   docker-compose up -d
   ```

4. **Выполните миграции (если нужно)**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Создайте суперпользователя**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Проверка работоспособности

После запуска проверьте статус сервисов:

```bash
docker-compose ps
```

Все сервисы должны быть в состоянии `Up`.


### Команды

```bash
# Просмотр логов
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Остановка проекта
docker-compose down

# Остановка с удалением volumes
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache

# Выполнение команд в контейнере
docker-compose exec web python manage.py shell
docker-compose exec db psql -U django_user -d djangorf
```

## Разработка
```bash
docker-compose up --build
```

## Лицензия
MIT