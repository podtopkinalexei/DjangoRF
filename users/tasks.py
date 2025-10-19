from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def check_inactive_users():
    """
    Проверка и блокировка пользователей, которые не заходили более месяца
    """
    try:
        # Вычисляем дату, до которой считаем пользователя активным
        threshold_date = timezone.now() - timedelta(days=30)

        # Находим пользователей, которые не заходили более месяца
        inactive_users = User.objects.filter(
            last_login__lt=threshold_date,
            is_active=True
        )

        count = inactive_users.count()

        # Блокируем пользователей
        inactive_users.update(is_active=False)

        return f"Заблокировано {count} неактивных пользователей"

    except Exception as e:
        return f"Ошибка при блокировке неактивных пользователей: {str(e)}"

