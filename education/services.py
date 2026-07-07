from dotenv import load_dotenv

from config.settings import STRIPE_CLIENT
from education.models import Course

load_dotenv()


def get_stripe_course_id(course: Course) -> str:
    """Возвращает уникальный Stripe-идентификатор курса"""

    product = STRIPE_CLIENT.v1.products.create(
        {
            "name": course.name,
            "metadata": {"course_id": course.pk, "owner_id": course.owner.pk},
            "default_price_data": {"unit_amount": course.usd_price, "currency": "usd"},
        }
    )
    return str(product["id"])
