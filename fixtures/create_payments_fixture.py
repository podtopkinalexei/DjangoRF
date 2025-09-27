import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Payment
from materials.models import Course, Lesson


def create_payments():
    # Создаем тестовые данные если их нет
    user, created = User.objects.get_or_create(
        email='testuser@example.com',
        defaults={'first_name': 'Test', 'last_name': 'User'}
    )

    course, created = Course.objects.get_or_create(
        title='Python для начинающих',
        defaults={'description': 'Базовый курс по Python'}
    )

    lesson, created = Lesson.objects.get_or_create(
        title='Введение в Python',
        defaults={'description': 'Первое знакомство с Python', 'course': course}
    )

    # Создаем платежи
    payments_data = [
        {
            'user': user,
            'paid_course': course,
            'paid_lesson': None,
            'amount': 10000.00,
            'payment_method': 'transfer'
        },
        {
            'user': user,
            'paid_course': None,
            'paid_lesson': lesson,
            'amount': 1500.00,
            'payment_method': 'cash'
        },
        {
            'user': user,
            'paid_course': course,
            'paid_lesson': None,
            'amount': 8000.00,
            'payment_method': 'transfer'
        },
    ]

    for payment_data in payments_data:
        payment, created = Payment.objects.get_or_create(
            user=payment_data['user'],
            paid_course=payment_data['paid_course'],
            paid_lesson=payment_data['paid_lesson'],
            defaults=payment_data
        )
        if created:
            print(f"Создан платеж: {payment}")


if __name__ == '__main__':
    create_payments()
