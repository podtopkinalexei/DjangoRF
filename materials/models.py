from django.db import models
from users.models import User

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    preview = models.ImageField(upload_to='courses/previews/', blank=True, null=True, verbose_name='Превью')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             verbose_name='Владелец', related_name='courses')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        permissions = [
            ("can_edit_course", "Can edit course"),
        ]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    preview = models.ImageField(upload_to='lessons/previews/', blank=True, null=True, verbose_name='Превью')
    video_link = models.URLField(blank=True, null=True, verbose_name='Ссылка на видео')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Курс')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             verbose_name='Владелец', related_name='lessons')

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        permissions = [
            ("can_edit_lesson", "Can edit lesson"),
        ]

    def __str__(self):
        return self.title


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscriptions'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='Курс',
        related_name='subscriptions'
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} подписан на {self.course.title}"


class Payment(models.Model):
    """
    Модель для хранения информации о платежах
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('transfer', 'Перевод на счет'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='payments'
    )
    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата платежа'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Оплаченный курс',
        related_name='payments'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Оплаченный урок',
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма оплаты'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='transfer',
        verbose_name='Способ оплаты'
    )

    # Поля для интеграции со Stripe
    stripe_product_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID продукта в Stripe'
    )
    stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID цены в Stripe'
    )
    stripe_session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID сессии в Stripe'
    )
    stripe_payment_link = models.URLField(
        blank=True,
        null=True,
        verbose_name='Ссылка на оплату в Stripe'
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='Оплачено'
    )

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Платеж {self.user.email} - {self.amount} руб."

    def clean(self):
        """
        Проверка, что оплачен либо курс, либо урок
        """
        if not self.course and not self.lesson:
            raise ValidationError('Должен быть указан курс или урок')
        if self.course and self.lesson:
            raise ValidationError('Можно указать только курс или только урок')