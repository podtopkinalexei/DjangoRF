from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveAPIView,
    LessonUpdateAPIView,
    LessonDestroyAPIView,
    SubscriptionAPIView,
    PaymentCreateAPIView,
    PaymentStatusAPIView,
    PaymentListAPIView,
    PaymentSuccessAPIView,
    PaymentCancelAPIView,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')

urlpatterns = [
    path('', include(router.urls)),
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonRetrieveAPIView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/update/', LessonUpdateAPIView.as_view(), name='lesson-update'),
    path('lessons/<int:pk>/delete/', LessonDestroyAPIView.as_view(), name='lesson-delete'),
    path('subscriptions/', SubscriptionAPIView.as_view(), name='subscription'),

    # Платежи
    path('payments/create/', PaymentCreateAPIView.as_view(), name='payment-create'),
    path('payments/status/', PaymentStatusAPIView.as_view(), name='payment-status'),
    path('payments/history/', PaymentListAPIView.as_view(), name='payment-list'),
    path('payments/success/', PaymentSuccessAPIView.as_view(), name='payment-success'),
    path('payments/cancel/', PaymentCancelAPIView.as_view(), name='payment-cancel'),
]