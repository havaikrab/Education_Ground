from dotenv import load_dotenv
from stripe.checkout import Session

from config.settings import STRIPE_CLIENT
from education.models import Course, Lesson, StripeProduct

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


def get_stripe_session(product: StripeProduct) -> Session:
    session = STRIPE_CLIENT.v1.checkout.sessions.create(
        {
            "success_url": "https://example.com/success",
            "line_items": [{"price": product.stripe_price_id, "quantity": 1}],
            "mode": "payment",
        }
    )
    return session
