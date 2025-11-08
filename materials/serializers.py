from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import YouTubeLinkValidator
from .models import Payment


class LessonSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['owner']

        validators = [
            YouTubeLinkValidator(field='video_link')
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['user', 'subscribed_at']


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['owner']

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на курс
        """
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(
                user=user,
                course=obj
            ).exists()
        return False


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'payment_date', 'course', 'course_title',
            'lesson', 'lesson_title', 'amount', 'payment_method', 'is_paid',
            'stripe_session_id', 'stripe_payment_link'
        ]
        read_only_fields = [
            'user', 'payment_date', 'is_paid', 'stripe_session_id',
            'stripe_payment_link'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания платежа
    """
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )

    def validate(self, attrs):
        course_id = attrs.get('course_id')
        lesson_id = attrs.get('lesson_id')

        if not course_id and not lesson_id:
            raise serializers.ValidationError(
                "Должен быть указан course_id или lesson_id"
            )

        if course_id and lesson_id:
            raise serializers.ValidationError(
                "Можно указать только course_id или только lesson_id"
            )

        return attrs


class PaymentStatusSerializer(serializers.Serializer):
    """
    Сериализатор для проверки статуса платежа
    """
    session_id = serializers.CharField(max_length=100)
    payment_status = serializers.CharField(max_length=20, read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    amount_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )