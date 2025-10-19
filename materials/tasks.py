from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Course, Subscription


@shared_task
def send_course_update_notification(course_id):
    """
    Отправка уведомлений об обновлении курса подписанным пользователям
    """
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(course=course)

        for subscription in subscriptions:
            send_mail(
                subject=f'Обновление курса: {course.title}',
                message=f'Уважаемый(ая) {subscription.user.email}!\n\n'
                        f'Курс "{course.title}" был обновлен. '
                        f'Загляните, чтобы ознакомиться с новыми материалами!\n\n'
                        f'С уважением, команда образовательной платформы',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=False,
            )

        return f"Уведомления отправлены для курса {course.title}"

    except Course.DoesNotExist:
        return f"Курс с ID {course_id} не найден"
    except Exception as e:
        return f"Ошибка при отправке уведомлений: {str(e)}"


@shared_task
def send_lesson_update_notification(lesson_id, course_id):
    """
    Отправка уведомлений об обновлении урока (с проверкой времени)
    """
    try:
        course = Course.objects.get(id=course_id)

        # Проверяем, когда курс обновлялся последний раз
        time_threshold = timezone.now() - timedelta(hours=4)

        # Если курс обновлялся менее 4 часов назад, не отправляем уведомление
        if course.updated_at and course.updated_at > time_threshold:
            return f"Курс обновлялся недавно, уведомление не отправлено"

        # Отправляем уведомления подписанным пользователям
        subscriptions = Subscription.objects.filter(course=course)

        for subscription in subscriptions:
            send_mail(
                subject=f'Новый урок в курсе: {course.title}',
                message=f'Уважаемый(ая) {subscription.user.email}!\n\n'
                        f'В курсе "{course.title}" добавлен новый урок. '
                        f'Не пропустите новые знания!\n\n'
                        f'С уважением, команда образовательной платформы',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=False,
            )

        # Обновляем время последнего обновления курса
        course.updated_at = timezone.now()
        course.save()

        return f"Уведомления об уроке отправлены для курса {course.title}"

    except Course.DoesNotExist:
        return f"Курс с ID {course_id} не найден"
    except Exception as e:
        return f"Ошибка при отправке уведомлений: {str(e)}"

