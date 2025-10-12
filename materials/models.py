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

