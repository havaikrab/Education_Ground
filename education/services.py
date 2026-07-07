from dotenv import load_dotenv

from config.settings import STRIPE_CLIENT
from education.models import Course, Lesson

load_dotenv()


def get_stripe_course_id(course: Course) -> str:
    """Возвращает уникальный Stripe-идентификатор курса"""

    product = STRIPE_CLIENT.v1.products.create(
        {"name": course.name, "metadata": {"course_id": course.pk, "owner_id": course.owner.pk}}
    )
    return str(product["id"])


def get_stripe_lesson_id(lesson: Lesson) -> str:
    """Возвращает уникальный Stripe-идентификатор урока"""

    product = STRIPE_CLIENT.v1.products.create(
        {"name": lesson.name, "metadata": {"lesson_id": lesson.pk, "owner_id": lesson.course.owner.pk}}
    )
    return str(product["id"])


def get_stripe_price_id(product: Course | Lesson, product_id: str) -> str:
    """Возвращает уникальный Stripe-идентификатор цены продукта"""

    price = STRIPE_CLIENT.v1.prices.create(
        {"currency": "usd", "unit_amount": product.usd_price, "product": product_id}
    )
    return str(price["id"])
