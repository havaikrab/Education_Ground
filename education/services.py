from datetime import datetime
from urllib.parse import urljoin

from django.utils import timezone as django_tz
from dotenv import load_dotenv
from stripe import Event

from config.settings import CURRENT_SITE, STRIPE_CLIENT
from education.models import Course, Lesson, Payment, StripeProduct, StripeSession, Subscription
from users.models import CustomUser

load_dotenv()


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
