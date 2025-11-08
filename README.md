## Учебный проект SkyPro "Decker"

### Предварительные требования

- Docker
- Docker Compose

### Локальный запуск проекта

1. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/podtopkinalexei/DjangoRF
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

4. **Выполните миграции**
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

#### Проверка отдельных сервисов:

- **Django приложение** - http://localhost:8000/api/
- **Админка Django** - http://localhost:8000/admin/
- **API документация** - http://localhost:8000/swagger/

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

## Настройка удаленного сервера для деплоя

### 1. Подготовка сервера

**Требования к серверу:**
- Ubuntu 20.04+ / Debian 11+
- Docker и Docker Compose
- Открытые порты: 80, 443, 22

### 2. Установка Docker на сервер

```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения изменений
newgrp docker
```

### 3. Настройка проекта на сервере

```bash
# Создание директории проекта
sudo mkdir -p /opt/django-rf-app
cd /opt/django-rf-app

# Создание docker-compose.yml
sudo nano docker-compose.yml
```

### 4. Создание .env файла на сервере

```bash
# Создание .env файла
sudo nano .env
```

### 5. Настройка прав доступа

```bash
# Изменение владельца директории
sudo chown -R $USER:$USER /opt/django-rf-app
chmod -R 755 /opt/django-rf-app
```

## Настройка GitHub Actions для автоматического деплоя

### 1. Добавление Secrets в GitHub

Зайдите в настройки репозитория GitHub:
`Settings → Secrets and variables → Actions`

Добавьте следующие secrets:

**Обязательные:**
- `SERVER_HOST` - IP адрес вашего сервера
- `SERVER_USERNAME` - пользователь для SSH (обычно `root` или `ubuntu`)
- `SERVER_SSH_KEY` - приватный SSH ключ для доступа к серверу
- `HEALTH_CHECK_URL` - URL для проверки здоровья (например, `http://your-server-ip:8000/api/`)

**Переменные окружения (для безопасности):**
- `DB_NAME` - имя базы данных
- `DB_USER` - пользователь базы данных
- `DB_PASSWORD` - пароль базы данных
- `SECRET_KEY` - секретный ключ Django
- `EMAIL_HOST_USER` - email для отправки
- `EMAIL_HOST_PASSWORD` - пароль от email
- `STRIPE_SECRET_KEY` - Stripe секретный ключ

### 2. Генерация SSH ключа для деплоя

```bash
# На локальной машине
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Публичный ключ добавьте на сервер
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub user@your-server-ip

# Приватный ключ добавьте в GitHub Secrets как SERVER_SSH_KEY
cat ~/.ssh/github_actions_deploy
```

### 3. Запуск workflow

Workflow автоматически запускается при:
- Push в ветки `main` или `master`
- Создании pull request в эти ветки

**Ручной запуск workflow:**
1. Перейдите в репозиторий на GitHub
2. `Actions` → `Django CI/CD Pipeline`
3. Нажмите `Run workflow`
4. Выберите ветку и запустите

### 4. Мониторинг деплоя

**Проверка статуса workflow:**
- Зайдите в `Actions` в вашем репозитории
- Выберите текущий running workflow
- Следите за выполнением каждого job

**Проверка на сервере после деплоя:**
```bash
# Проверка работающих контейнеров
docker ps

# Просмотр логов
docker logs django_rf_web_prod

# Проверка здоровья приложения
curl http://localhost:8000/api/health/
```

## Структура CI/CD Pipeline

### 1. Тестирование (Test Job)
- Запуск PostgreSQL и Redis для тестов
- Установка зависимостей
- Запуск миграций
- Выполнение тестов Django
- Проверка безопасности кода

### 2. Сборка и деплой (Build and Deploy Job)
- Сборка Docker образа
- Пуш образа в GitHub Container Registry
- SSH подключение к серверу
- Остановка старых контейнеров
- Запуск новых контейнеров
- Выполнение миграций
- Сбор статических файлов


## Лицензия
MIT
```
