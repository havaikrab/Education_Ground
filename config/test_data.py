from education.models import Course, Lesson
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


def course_test_data() -> dict:
    """Возвращает тестовые данные для создания объектов модели Course"""

    return {
        "user_1_a": {
            "name": "course_1",
            "description": "description of course_1",
        },
        "user_2_b": {
            "name": "course_2",
            "description": "description of course_2",
        },
        "user_2_c": {
            "name": "course_3",
            "description": "description of course_3",
        },
        "user_3_d": {
            "name": "course_4",
            "description": "description of course_4",
        },
        "user_3_e": {
            "name": "course_5",
            "description": "description of course_5",
        },
        "user_3_f": {
            "name": "course_6",
            "description": "description of course_6",
        },
        "user_4_g": {
            "name": "course_7",
            "description": "description of course_7",
        },
        "user_4_h": {
            "name": "course_8",
            "description": "description of course_8",
        },
        "user_4_i": {
            "name": "course_9",
            "description": "description of course_9",
        },
        "user_4_j": {
            "name": "course_10",
            "description": "description of course_10",
        },
    }


def lesson_test_data() -> dict:
    """Возвращает тестовые данные для создания объектов модели Lesson"""

    return {
        "course_1_a": {
            "name": "lesson_1",
            "description": "description of lesson_1",
            "link_to_video": "youtube.com/lesson_1",
        },
        "course_2_b": {
            "name": "lesson_2",
            "description": "description of lesson_2",
            "link_to_video": "youtube.com/lesson_2",
        },
        "course_2_c": {
            "name": "lesson_3",
            "description": "description of lesson_3",
            "link_to_video": "youtube.com/lesson_3",
        },
        "course_3_d": {
            "name": "lesson_4",
            "description": "description of lesson_4",
            "link_to_video": "youtube.com/lesson_4",
        },
        "course_3_e": {
            "name": "lesson_5",
            "description": "description of lesson_5",
            "link_to_video": "youtube.com/lesson_5",
        },
        "course_3_f": {
            "name": "lesson_6",
            "description": "description of lesson_6",
            "link_to_video": "youtube.com/lesson_6",
        },
        "course_5_g": {
            "name": "lesson_7",
            "description": "description of lesson_7",
            "link_to_video": "youtube.com/lesson_7",
        },
        "course_6_h": {
            "name": "lesson_8",
            "description": "description of lesson_8",
            "link_to_video": "youtube.com/lesson_8",
        },
        "course_6_i": {
            "name": "lesson_9",
            "description": "description of lesson_9",
            "link_to_video": "youtube.com/lesson_9",
        },
        "course_7_j": {
            "name": "lesson_10",
            "description": "description of lesson_10",
            "link_to_video": "youtube.com/lesson_10",
        },
        "course_7_k": {
            "name": "lesson_11",
            "description": "description of lesson_11",
            "link_to_video": "youtube.com/lesson_11",
        },
        "course_7_l": {
            "name": "lesson_12",
            "description": "description of lesson_12",
            "link_to_video": "youtube.com/lesson_12",
        },
        "course_9_m": {
            "name": "lesson_13",
            "description": "description of lesson_13",
            "link_to_video": "youtube.com/lesson_13",
        },
        "course_10_n": {
            "name": "lesson_14",
            "description": "description of lesson_14",
            "link_to_video": "youtube.com/lesson_14",
        },
        "course_10_o": {
            "name": "lesson_15",
            "description": "description of lesson_15",
            "link_to_video": "youtube.com/lesson_15",
        },
    }


def set_users_data() -> None:
    """Наполняет тестовую базу данных объектами модели CustomUser"""

    users = [CustomUser(**user) for user in customuser_test_data()]
    CustomUser.objects.bulk_create(users)


def set_courses_data() -> None:
    """Наполняет тестовую базу данных связанными объектами моделей CustomUser, Course"""

    set_users_data()
    courses = course_test_data()
    for k, v in courses.items():
        owner = CustomUser.objects.get(username=k[:-2])
        Course.objects.create(owner=owner, **v)


def set_lessons_data() -> None:
    """Наполняет тестовую базу данных связанными объектами моделей CustomUser, Course, Lesson"""

    set_courses_data()
    lessons = lesson_test_data()
    for k, v in lessons.items():
        course = Course.objects.get(name=k[:-2])
        Lesson.objects.create(course=course, **v)
