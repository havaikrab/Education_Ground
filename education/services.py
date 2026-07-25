from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from django.db.models import Q
from django.utils import timezone
from django.utils import timezone as django_tz
from stripe import Event

from config.settings import CURRENT_SITE, STRIPE_CLIENT
from education.models import Course, Lesson, Payment, StripeProduct, StripeSession, Subscription
from users.models import CustomUser

from .tasks import send_notices


def get_stripe_course_data(course: Course) -> dict:
    """Возвращает данные для создания Stripe-продукта курса"""

    product = STRIPE_CLIENT.v1.products.create(
        {"name": course.name, "metadata": {"course_id": course.pk, "owner_id": course.owner.pk}}
    )
    price = STRIPE_CLIENT.v1.prices.create(
        {"currency": "usd", "unit_amount": course.usd_price, "product": product["id"]}
    )
    return {"stripe_product_id": product["id"], "stripe_price_id": price["id"]}


def get_stripe_lesson_data(lesson: Lesson) -> dict:
    """Возвращает данные для создания Stripe-продукта урока"""

    product = STRIPE_CLIENT.v1.products.create(
        {"name": lesson.name, "metadata": {"lesson_id": lesson.pk, "owner_id": lesson.course.owner.pk}}
    )
    price = STRIPE_CLIENT.v1.prices.create(
        {"currency": "usd", "unit_amount": lesson.usd_price, "product": product["id"]}
    )
    return {"stripe_product_id": product["id"], "stripe_price_id": price["id"]}


def get_stripe_session(product: StripeProduct, user: CustomUser) -> StripeSession:
    """Создает объект Stripe-сессии"""

    session = STRIPE_CLIENT.v1.checkout.sessions.create(
        {
            "success_url": urljoin(CURRENT_SITE, "/payment_success/?session_id={CHECKOUT_SESSION_ID}"),
            "cancel_url": urljoin(CURRENT_SITE, "/courses/"),
            "line_items": [{"price": product.stripe_price_id, "quantity": 1}],
            "mode": "payment",
            "client_reference_id": str(user.pk),
            "metadata": {"product_type": product.product_type, "product_id": str(product.pk)},
        }
    )
    stripe_session = StripeSession.objects.create(
        session_id=session.id, session_url=session.url, customer=user, product=product
    )
    return stripe_session


def update_stripe_session_status(session: StripeSession) -> StripeSession:
    """Обновляет статус сессии в соответствии с данными в сервисе Stripe"""

    stripe_session = STRIPE_CLIENT.v1.checkout.sessions.retrieve(session.session_id)
    session.status = stripe_session["status"]
    session.save()
    return session


def parse_webhook_event(event: Event) -> None:
    """Разбирает Stripe-Event объект и сохраняет основные данные в БД"""

    event_type = event.type
    if event_type in ["checkout.session.completed", "checkout.session.expired"]:
        session_id = event.data.object.id
        session = StripeSession.objects.select_related("customer", "product").get(session_id=session_id)
        session.status = event.data.object.status
        session.save()
        if event_type == "checkout.session.completed":
            customer = session.customer
            paid_at = event.created
            created_at = datetime.fromtimestamp(paid_at, tz=django_tz.UTC)  # type: ignore
            stripe_product = session.product
            paid_amount = event.data.object.amount_total
            Payment.objects.create(
                payer=customer,
                created_at=created_at,
                stripe_product=stripe_product,
                amount=paid_amount,
                method="cashless",
            )
            product_type = event.data.object.metadata.product_type
            if product_type == "course":
                Subscription.objects.get_or_create(subscriber=customer, course=stripe_product.course)


def manage_updating(course: Course, lesson: Optional[Lesson] = None, new_course: Optional[Course] = None) -> None:
    """Проверяет дату последнего обновления курса и запускает рассылку уведомлений пользователям-подписчикам,
    если курс был обновлен более 4-х часов назад"""

    current_course_product = course.stripe_courses.get(is_active=True)  # type: ignore
    hours_ago = (timezone.now() - current_course_product.created_at).total_seconds() / 3600
    if hours_ago > 4:
        if lesson:
            message = f'Материалы урока "{lesson.name}" обновлены.'
            if new_course:
                recipients = CustomUser.objects.filter(
                    Q(subscriptions__course=course)
                    | Q(subscriptions__course=new_course)
                    | Q(payments__stripe_product__lesson=lesson)
                ).distinct()
            else:
                recipients = CustomUser.objects.filter(
                    Q(subscriptions__course=course) | Q(payments__stripe_product__lesson=lesson)
                ).distinct()
        else:
            recipients = CustomUser.objects.filter(subscriptions__course=course)
            message = f'Материалы курса "{course.name}" обновлены.'
        emails = [recipient.email for recipient in recipients]
        send_notices.delay(emails, message)
    stripe_data = get_stripe_course_data(course)
    StripeProduct.objects.create(course=course, **stripe_data)
