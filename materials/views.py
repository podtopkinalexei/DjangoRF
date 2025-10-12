from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course, Lesson, Subscription
from .paginators import CoursePagination, LessonPagination
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer
from .permissions import IsOwnerOrModerator, IsModerator, IsOwner


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CoursePagination

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.groups.filter(name='moderators').exists():
            # Модераторы видят все курсы
            return Course.objects.all()
        elif user.is_authenticated:
            # Обычные пользователи видят только свои курсы
            return Course.objects.filter(owner=user)
        return Course.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            # Создавать курсы могут только авторизованные пользователи (не модераторы)
            return [permissions.IsAuthenticated() & ~IsModerator()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Обновлять и удалять могут только владельцы
            return [IsOwner()]
        else:
            # Просматривать могут все авторизованные
            return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
        """
        Передаем request в контекст сериализатора
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LessonPagination

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            # Модераторы видят все уроки
            return Lesson.objects.all()
        else:
            # Обычные пользователи видят только свои уроки
            return Lesson.objects.filter(owner=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            # Создавать уроки могут только не модераторы
            return [permissions.IsAuthenticated() & ~IsModerator()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonUpdateAPIView(generics.UpdateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonDestroyAPIView(generics.DestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Удалять могут только владельцы, поэтому показываем только свои уроки
        return Lesson.objects.filter(owner=self.request.user)


class SubscriptionAPIView(APIView):
    """
    APIView для управления подписками на курсы
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Создание или удаление подписки
        """
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Курс не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем существующую подписку
        subscription = Subscription.objects.filter(
            user=user,
            course=course
        ).first()

        if subscription:
            # Удаляем подписку
            subscription.delete()
            return Response(
                {"message": "Подписка удалена"},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            # Создаем подписку
            subscription = Subscription.objects.create(
                user=user,
                course=course
            )
            serializer = SubscriptionSerializer(subscription)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

