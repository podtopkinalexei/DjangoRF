import os
import stripe
from django.core.exceptions import ValidationError

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

HOST = os.getenv('HOST')

class StripeService:
    """
    Сервис для работы с Stripe API
    """

    @staticmethod
    def create_product(name, description=None):
        """
        Создание продукта в Stripe
        """
        try:
            product = stripe.Product.create(
                name=name,
                description=description
            )
            return product
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка создания продукта в Stripe: {e}")

    @staticmethod
    def create_price(product_id, amount, currency='rub'):
        """
        Создание цены в Stripe
        amount: сумма в рублях (будет преобразована в копейки)
        """
        try:
            # Преобразуем рубли в копейки
            amount_in_cents = int(amount * 100)

            price = stripe.Price.create(
                product=product_id,
                unit_amount=amount_in_cents,
                currency=currency,
            )
            return price
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка создания цены в Stripe: {e}")

    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url, metadata=None):
        """
        Создание сессии оплаты в Stripe
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            return session
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка создания сессии оплаты в Stripe: {e}")

    @staticmethod
    def retrieve_session(session_id):
        """
        Получение информации о сессии
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка получения сессии из Stripe: {e}")


class PaymentService:
    """
    Сервис для работы с платежами
    """

    @staticmethod
    def create_payment_intent(user, course=None, lesson=None, amount=None):
        """
        Создание намерения платежа и подготовка данных для Stripe
        """
        from .models import Payment

        # Определяем объект оплаты и сумму
        if course:
            payment_object = course
            if not amount:
                amount = 1000  # Пример: 1000 рублей за курс
            object_type = 'course'
        elif lesson:
            payment_object = lesson
            if not amount:
                amount = 500  # Пример: 500 рублей за урок
            object_type = 'lesson'
        else:
            raise ValidationError('Должен быть указан курс или урок')

        # Создаем продукт в Stripe
        stripe_service = StripeService()
        product = stripe_service.create_product(
            name=payment_object.title,
            description=payment_object.description
        )

        # Создаем цену в Stripe
        price = stripe_service.create_price(
            product_id=product.id,
            amount=amount
        )

        # Создаем URL для редиректа
        success_url = f"{HOST}/api/payments/success/?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{HOST}/api/payments/cancel/"

        # Метаданные для идентификации платежа
        metadata = {
            'user_id': user.id,
            'object_type': object_type,
            'object_id': payment_object.id
        }

        # Создаем сессию оплаты
        session = stripe_service.create_checkout_session(
            price_id=price.id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )

        # Создаем запись о платеже в базе данных
        payment = Payment.objects.create(
            user=user,
            course=course,
            lesson=lesson,
            amount=amount,
            payment_method='transfer',
            stripe_product_id=product.id,
            stripe_price_id=price.id,
            stripe_session_id=session.id,
            stripe_payment_link=session.url,
            is_paid=False
        )

        return {
            'payment_id': payment.id,
            'payment_link': session.url,
            'session_id': session.id,
            'amount': amount
        }

    @staticmethod
    def check_payment_status(session_id):
        """
        Проверка статуса платежа
        """
        from .models import Payment

        stripe_service = StripeService()
        session = stripe_service.retrieve_session(session_id)

        # Находим соответствующий платеж
        try:
            payment = Payment.objects.get(stripe_session_id=session_id)
            if session.payment_status == 'paid' and not payment.is_paid:
                payment.is_paid = True
                payment.save()

            return {
                'session_id': session_id,
                'payment_status': session.payment_status,
                'is_paid': payment.is_paid,
                'amount_total': session.amount_total / 100  # Преобразуем обратно в рубли
            }
        except Payment.DoesNotExist:
            raise ValidationError('Платеж не найден')

