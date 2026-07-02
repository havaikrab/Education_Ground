from django.utils import timezone

from education.models import Course, Lesson, Payment, Subscription
from users.models import CustomUser


def customuser_test_data() -> list:
    """Возвращает тестовые данные для создания объектов модели CustomUser"""

    return [
        {
            "username": "user_1",
            "email": "user_1@mail.py",
            "password": "user_1_password",
            "first_name": "Anton",
            "last_name": "Chekhov",
            "phone": "unknown",
            "city": "Boston",
        },
        {
            "username": "user_2",
            "email": "user_2@mail.py",
            "password": "user_2_password",
            "first_name": "Fedor",
            "last_name": "Dostoevsky",
            "phone": "black",
            "city": "Petersburg",
        },
        {
            "username": "user_3",
            "email": "user_3@mail.py",
            "password": "user_3_password",
            "first_name": "Mike",
            "last_name": "Lomonosov",
            "phone": "89998887766",
        },
        {
            "username": "user_4",
            "email": "user_4@mail.py",
            "password": "user_4_password",
            "first_name": "Alexandre",
            "last_name": "Dumas",
            "phone": "1234567",
            "city": "Paris",
        },
        {
            "username": "user_5",
            "email": "user_5@mail.py",
            "password": "user_5_password",
            "first_name": "Petr",
            "last_name": "Petrov",
            "phone": "i-phone",
            "city": "Moscow",
        },
    ]


def course_test_data() -> list:
    """Возвращает тестовые данные для создания объектов модели Course"""

    return [
        {"name": "course_1", "description": "description of course_1", "owner": "user_1"},
        {"name": "course_2", "description": "description of course_2", "owner": "user_2"},
        {"name": "course_3", "description": "description of course_3", "owner": "user_2"},
        {"name": "course_4", "description": "description of course_4", "owner": "user_3"},
        {"name": "course_5", "description": "description of course_5", "owner": "user_3"},
        {"name": "course_6", "description": "description of course_6", "owner": "user_3"},
        {"name": "course_7", "description": "description of course_7", "owner": "user_4"},
        {"name": "course_8", "description": "description of course_8", "owner": "user_4"},
        {"name": "course_9", "description": "description of course_9", "owner": "user_4"},
        {"name": "course_10", "description": "description of course_10", "owner": "user_4"},
    ]


def lesson_test_data() -> list:
    """Возвращает тестовые данные для создания объектов модели Lesson"""

    return [
        {
            "name": "lesson_1",
            "description": "description of lesson_1",
            "link_to_video": "youtube.com/lesson_1",
            "course": "course_1",
        },
        {
            "name": "lesson_2",
            "description": "description of lesson_2",
            "link_to_video": "youtube.com/lesson_2",
            "course": "course_2",
        },
        {
            "name": "lesson_3",
            "description": "description of lesson_3",
            "link_to_video": "youtube.com/lesson_3",
            "course": "course_2",
        },
        {
            "name": "lesson_4",
            "description": "description of lesson_4",
            "link_to_video": "youtube.com/lesson_4",
            "course": "course_3",
        },
        {
            "name": "lesson_5",
            "description": "description of lesson_5",
            "link_to_video": "youtube.com/lesson_5",
            "course": "course_3",
        },
        {
            "name": "lesson_6",
            "description": "description of lesson_6",
            "link_to_video": "youtube.com/lesson_6",
            "course": "course_3",
        },
        {
            "name": "lesson_7",
            "description": "description of lesson_7",
            "link_to_video": "youtube.com/lesson_7",
            "course": "course_5",
        },
        {
            "name": "lesson_8",
            "description": "description of lesson_8",
            "link_to_video": "youtube.com/lesson_8",
            "course": "course_6",
        },
        {
            "name": "lesson_9",
            "description": "description of lesson_9",
            "link_to_video": "youtube.com/lesson_9",
            "course": "course_6",
        },
        {
            "name": "lesson_10",
            "description": "description of lesson_10",
            "link_to_video": "youtube.com/lesson_10",
            "course": "course_7",
        },
        {
            "name": "lesson_11",
            "description": "description of lesson_11",
            "link_to_video": "youtube.com/lesson_11",
            "course": "course_7",
        },
        {
            "name": "lesson_12",
            "description": "description of lesson_12",
            "link_to_video": "youtube.com/lesson_12",
            "course": "course_7",
        },
        {
            "name": "lesson_13",
            "description": "description of lesson_13",
            "link_to_video": "youtube.com/lesson_13",
            "course": "course_9",
        },
        {
            "name": "lesson_14",
            "description": "description of lesson_14",
            "link_to_video": "youtube.com/lesson_14",
            "course": "course_10",
        },
        {
            "name": "lesson_15",
            "description": "description of lesson_15",
            "link_to_video": "youtube.com/lesson_15",
            "course": "course_10",
        },
    ]


def payment_test_data() -> list:
    """Возвращает тестовые данные для создания объектов модели Payment"""

    return [
        {
            "payer": "user_5",
            "created_at": timezone.now(),
            "paid_course": "course_10",
            "amount": 3000,
            "method": "cashless",
        },
        {"payer": "user_5", "created_at": timezone.now(), "paid_course": "course_10", "amount": 333, "method": "cash"},
        {"payer": "user_5", "created_at": timezone.now(), "paid_lesson": "lesson_13", "amount": 100, "method": "cash"},
        {
            "payer": "user_5",
            "created_at": timezone.now(),
            "paid_lesson": "lesson_12",
            "amount": 200,
            "method": "cashless",
        },
        {"payer": "user_1", "created_at": timezone.now(), "paid_lesson": "lesson_15", "amount": 300, "method": "cash"},
        {
            "payer": "user_1",
            "created_at": timezone.now(),
            "paid_course": "course_9",
            "amount": 2000,
            "method": "cashless",
        },
        {
            "payer": "user_1",
            "created_at": timezone.now(),
            "paid_course": "course_8",
            "amount": 1,
            "method": "cashless",
        },
        {"payer": "user_2", "created_at": timezone.now(), "paid_course": "course_6", "amount": 4000, "method": "cash"},
        {"payer": "user_2", "created_at": timezone.now(), "paid_lesson": "lesson_7", "amount": 400, "method": "cash"},
        {
            "payer": "user_3",
            "created_at": timezone.now(),
            "paid_lesson": "lesson_1",
            "amount": 500,
            "method": "cashless",
        },
    ]


def subscription_test_data() -> list:
    """Возвращает тестовые данные для создания объектов модели Subscription"""

    return [
        {"subscriber": "user_1", "course": "course_10"},
        {"subscriber": "user_1", "course": "course_9"},
        {"subscriber": "user_1", "course": "course_8"},
        {"subscriber": "user_2", "course": "course_7"},
        {"subscriber": "user_2", "course": "course_4"},
        {"subscriber": "user_3", "course": "course_10"},
        {"subscriber": "user_5", "course": "course_9"},
        {"subscriber": "user_5", "course": "course_5"},
        {"subscriber": "user_5", "course": "course_3"},
        {"subscriber": "user_5", "course": "course_1"},
    ]


def set_users_data() -> None:
    """Наполняет тестовую базу данных объектами модели CustomUser"""

    users = [CustomUser(**user) for user in customuser_test_data()]
    CustomUser.objects.bulk_create(users)


def set_courses_data() -> None:
    """Наполняет тестовую базу данных связанными объектами моделей CustomUser, Course"""

    set_users_data()
    courses = course_test_data()
    for course in courses:
        username = course.pop("owner")
        owner = CustomUser.objects.get(username=username)
        Course.objects.create(owner=owner, **course)


def set_lessons_data() -> None:
    """Наполняет тестовую базу данных связанными объектами моделей CustomUser, Course, Lesson"""

    set_courses_data()
    lessons = lesson_test_data()
    for lesson in lessons:
        course_name = lesson.pop("course")
        course = Course.objects.get(name=course_name)
        Lesson.objects.create(course=course, **lesson)


def set_payments_data() -> None:
    """Наполняет тестовую базу данных связанными объектами моделей CustomUser, Course, Lesson, Payment"""

    set_lessons_data()
    payments = payment_test_data()
    for payment in payments:
        payer_name = payment.pop("payer")
        payer = CustomUser.objects.get(username=payer_name)
        course_name = payment.pop("paid_course", None)
        lesson_name = payment.pop("paid_lesson", None)
        if course_name is not None:
            course = Course.objects.get(name=course_name)
            Payment.objects.create(payer=payer, paid_course=course, **payment)
        if lesson_name is not None:
            lesson = Lesson.objects.get(name=lesson_name)
            Payment.objects.create(payer=payer, paid_lesson=lesson, **payment)


def set_subscriptions_data() -> None:
    """Наполняет тестовую базу данных связанными объектами моделей CustomUser, Course, Lesson, Payment, Subscription"""

    set_payments_data()
    subscriptions = subscription_test_data()
    for subscription in subscriptions:
        subscriber = CustomUser.objects.get(username=subscription["subscriber"])
        course = Course.objects.get(name=subscription["course"])
        Subscription.objects.create(subscriber=subscriber, course=course)
