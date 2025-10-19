from rest_framework import viewsets, generics, permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import send_course_update_notification, send_lesson_update_notification

from .models import Course, Lesson, Subscription, Payment
from .paginators import CoursePagination, LessonPagination
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer, PaymentCreateSerializer, \
    PaymentStatusSerializer, PaymentSerializer
from .permissions import IsOwnerOrModerator, IsModerator, IsOwner
from .services import PaymentService


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
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_update(self, serializer):
        instance = serializer.save()
        # Асинхронная отправка уведомлений об обновлении курса
        send_course_update_notification.delay(instance.id)


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

    def perform_update(self, serializer):
        instance = serializer.save()
        # Асинхронная отправка уведомлений об обновлении урока
        send_lesson_update_notification.delay(instance.id, instance.course.id)


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


class PaymentCreateAPIView(APIView):
    """
    Создание платежа и получение ссылки на оплату
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                from .models import Course, Lesson

                course_id = serializer.validated_data.get('course_id')
                lesson_id = serializer.validated_data.get('lesson_id')
                amount = serializer.validated_data.get('amount')

                course = None
                lesson = None

                if course_id:
                    try:
                        course = Course.objects.get(id=course_id)
                    except Course.DoesNotExist:
                        return Response(
                            {'error': 'Курс не найден'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                if lesson_id:
                    try:
                        lesson = Lesson.objects.get(id=lesson_id)
                    except Lesson.DoesNotExist:
                        return Response(
                            {'error': 'Урок не найден'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                # Создаем платеж и получаем ссылку на оплату
                payment_data = PaymentService.create_payment_intent(
                    user=request.user,
                    course=course,
                    lesson=lesson,
                    amount=amount
                )

                return Response(payment_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentStatusAPIView(APIView):
    """
    Проверка статуса платежа
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response(
                {'error': 'session_id обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            status_data = PaymentService.check_payment_status(session_id)
            serializer = PaymentStatusSerializer(status_data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentListAPIView(ListAPIView):
    """
    Список платежей пользователя
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class PaymentSuccessAPIView(APIView):
    """
    Обработка успешной оплаты (редирект от Stripe)
    """

    def get(self, request):
        session_id = request.GET.get('session_id')
        if session_id:
            try:
                status_data = PaymentService.check_payment_status(session_id)
                return Response({
                    'message': 'Оплата прошла успешно!',
                    'status': status_data
                })
            except Exception as e:
                return Response({
                    'error': f'Ошибка при проверке платежа: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Спасибо за оплату!'
        })


class PaymentCancelAPIView(APIView):
    """
    Обработка отмены оплаты (редирект от Stripe)
    """

    def get(self, request):
        return Response({
            'message': 'Оплата была отменена. Вы можете попробовать снова.'
        }, status=status.HTTP_200_OK)

