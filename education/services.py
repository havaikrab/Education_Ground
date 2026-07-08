from urllib.parse import urljoin

from dotenv import load_dotenv

from config.settings import CURRENT_SITE, STRIPE_CLIENT
from education.models import Course, Lesson, StripeProduct, StripeSession
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
