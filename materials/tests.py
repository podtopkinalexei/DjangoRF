from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Course, Lesson, Subscription

User = get_user_model()


class LessonCRUDTestCase(APITestCase):
    """
    Тесты CRUD операций для уроков
    """

    def setUp(self):
        # Создаем тестовых пользователей
        self.owner_user = User.objects.create_user(
            email='owner@test.com',
            password='testpass123'
        )
        self.moderator_user = User.objects.create_user(
            email='moderator@test.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123'
        )

        # Создаем группу модераторов
        moderators_group, created = Group.objects.get_or_create(name='moderators')
        self.moderator_user.groups.add(moderators_group)

        # Создаем тестовый курс
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.owner_user
        )

        # Создаем тестовый урок
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            description='Test Lesson Description',
            video_link='https://www.youtube.com/watch?v=test123',
            course=self.course,
            owner=self.owner_user
        )

    def test_lesson_list_owner(self):
        """Владелец видит свои уроки"""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(reverse('lesson-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Используем results из-за пагинации

    def test_lesson_list_moderator(self):
        """Модератор видит все уроки"""
        self.client.force_authenticate(user=self.moderator_user)
        response = self.client.get(reverse('lesson-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lesson_create_owner(self):
        """Владелец может создавать уроки"""
        self.client.force_authenticate(user=self.owner_user)
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_link': 'https://www.youtube.com/watch?v=new123',
            'course': self.course.id
        }
        response = self.client.post(reverse('lesson-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_lesson_create_moderator_forbidden(self):
        """Модератор не может создавать уроки"""
        self.client.force_authenticate(user=self.moderator_user)
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_link': 'https://www.youtube.com/watch?v=new123',
            'course': self.course.id
        }
        response = self.client.post(reverse('lesson-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_update_owner(self):
        """Владелец может обновлять свои уроки"""
        self.client.force_authenticate(user=self.owner_user)
        data = {
            'title': 'Updated Lesson'
        }
        response = self.client.patch(
            reverse('lesson-update', kwargs={'pk': self.lesson.id}),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lesson_update_moderator(self):
        """Модератор может обновлять любые уроки"""
        self.client.force_authenticate(user=self.moderator_user)
        data = {
            'title': 'Updated by Moderator'
        }
        response = self.client.patch(
            reverse('lesson-update', kwargs={'pk': self.lesson.id}),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lesson_delete_owner(self):
        """Владелец может удалять свои уроки"""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.delete(
            reverse('lesson-delete', kwargs={'pk': self.lesson.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_lesson_delete_other_user_forbidden(self):
        """Другой пользователь не может удалять чужие уроки"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(
            reverse('lesson-delete', kwargs={'pk': self.lesson.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_youtube_link_validation(self):
        """Валидация YouTube ссылок"""
        self.client.force_authenticate(user=self.owner_user)
        data = {
            'title': 'Invalid Link Lesson',
            'description': 'Test Description',
            'video_link': 'https://vimeo.com/test123',  # Не YouTube ссылка
            'course': self.course.id
        }
        response = self.client.post(reverse('lesson-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_link', response.data)


class SubscriptionTestCase(APITestCase):
    """
    Тесты функционала подписок
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

    def test_subscription_create(self):
        """Создание подписки"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('subscription'),
            {'course_id': self.course.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                course=self.course
            ).exists()
        )

    def test_subscription_delete(self):
        """Удаление подписки"""
        # Сначала создаем подписку
        subscription = Subscription.objects.create(
            user=self.user,
            course=self.course
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('subscription'),
            {'course_id': self.course.id}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user,
                course=self.course
            ).exists()
        )

    def test_is_subscribed_field(self):
        """Проверка поля is_subscribed в сериализаторе курса"""
        # Создаем подписку
        Subscription.objects.create(user=self.user, course=self.course)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse('courses-detail', kwargs={'pk': self.course.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])

    def test_subscription_unique_together(self):
        """Проверка уникальности подписки"""
        Subscription.objects.create(user=self.user, course=self.course)

        # Попытка создать дубликат
        with self.assertRaises(Exception):
            Subscription.objects.create(user=self.user, course=self.course)


class PaginationTestCase(APITestCase):
    """
    Тесты пагинации
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        self.course = Course.objects.create(
            title='Test Course',
            owner=self.user
        )

        # Создаем несколько уроков для тестирования пагинации
        for i in range(15):
            Lesson.objects.create(
                title=f'Lesson {i}',
                description=f'Description {i}',
                course=self.course,
                owner=self.user
            )

    def test_lesson_pagination(self):
        """Тест пагинации уроков"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('lesson-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)  # page_size = 10

    def test_course_pagination(self):
        """Тест пагинации курсов"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('courses-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
