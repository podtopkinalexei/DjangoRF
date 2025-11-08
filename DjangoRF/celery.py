import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoRF.settings')

app = Celery('DjangoRF')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-inactive-users-monthly': {
        'task': 'users.tasks.check_inactive_users',
        'schedule': crontab(0, 0, day_of_month='1'),  # Первое число каждого месяца в полночь
    },
    'check-inactive-users-daily': {
        'task': 'users.tasks.check_inactive_users',
        'schedule': crontab(hour=0, minute=0),  # Ежедневно в полночь (для тестирования)
    },
}

