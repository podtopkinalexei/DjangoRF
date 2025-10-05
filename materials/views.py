from rest_framework import viewsets, generics, permissions
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from .permissions import IsOwnerOrModerator, IsModerator, IsOwner


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

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


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

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