import json
from typing import Any
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from stripe import Event

from education.models import Course, Lesson, Payment, StripeProduct, StripeSession, Subscription
from users.models import CustomUser


class CourseTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Course"""

    fixtures = ["course_fixture.json", "customuser_fixture.json", "lesson_fixture.json", "stripeproduct_fixture.json"]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.moderators = Group.objects.create(name="Модераторы")
        self.user = CustomUser.objects.get(email="user_4@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_course_creating(self) -> None:
        """Тест запроса на создание объекта модели Course"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        url = reverse("education:course-list")
        response = self.client.post(
            url,
            data={
                "name": "test_course",
                "description": "test_description with valid link https://youtube.com",
                "usd_price": 555,
            },
        )
        data = response.json()
        courses_count = Course.objects.count()
        self.assertEqual(courses_count, 11)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data.get("owner"), self.user.pk)
        self.assertEqual(data.get("name"), "test_course")
        self.assertEqual(len(StripeProduct.objects.all()), 26)
        stripe_product = StripeProduct.objects.get(course__name="test_course")
        self.assertEqual(stripe_product.lesson, None)
        self.assertEqual(stripe_product.is_active, True)
        self.assertEqual(stripe_product.owner_email, "user_4@mail.py")
        self.assertEqual(stripe_product.product_price, 555)

    def test_course_creating_with_invalid_link(self) -> None:
        """Тест запроса с невалидными данными на создание объекта модели Course"""

        url = reverse("education:course-list")
        response = self.client.post(
            url, data={"name": "invalid_course", "description": "test_description with invalid link vk.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_getting_own_course_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Course их владельцу"""

        user_id = self.user.pk
        url = f"/courses/?preview=False&owner={user_id}&subscription=False&paid=False&ordering=id&page_size=4"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 4)
        self.assertEqual(data["next"], None)
        for result in data["results"]:
            self.assertEqual(result["relation_status"], "owner")

    def test_getting_not_own_course_list(self) -> None:
        """Тест запроса на отображение чужого списка объектов модели Course"""

        random_user = CustomUser.objects.get(username="user_3")
        url = f"/courses/?owner={random_user.pk}"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 3)
        names = set()
        prices_sum = 0
        for result in data["results"]:
            self.assertEqual(result["relation_status"], "undefined")
            self.assertEqual(len(result), 6)
            names.add(result["name"])
            prices_sum += result["usd_price"]
        self.assertEqual(names, {"course_4", "course_5", "course_6"})
        self.assertEqual(prices_sum, 199998)

    def test_course_forbidden_retrieve(self) -> None:
        """Тест запроса на отображение объекта модели Course пользователю, не имеющему права на просмотр"""

        course = Course.objects.get(name="course_1")
        url = f"/courses/{course.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_retrieve_for_moderator(self) -> None:
        """Тест запроса на отображение объекта модели Course пользователю-модератору"""

        course = Course.objects.get(name="course_1")
        self.user.groups.add(self.moderators)
        url = f"/courses/{course.pk}/"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": course.pk,
                "name": "course_1",
                "description": f"{course.description}",
                "owner": course.owner.pk,
                "preview": None,
                "lessons_count": 1,
                "lessons_details": [
                    {
                        "id": 1,
                        "description": "description of lesson_1",
                        "link_to_video": "youtube.com/lesson_1",
                        "name": "lesson_1",
                        "preview": None,
                        "usd_price": 15000,
                        "course": 1,
                    }
                ],
                "relation_status": "undefined",
                "usd_price": 111111,
            },
        )

    def test_course_updating(self) -> None:
        """Тест запроса на изменение объекта модели Course владельцем"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        course = Course.objects.get(name="course_10")
        self.assertEqual(len(StripeProduct.objects.filter(course=course)), 1)
        stripe_product = StripeProduct.objects.get(course=course)
        self.assertEqual(stripe_product.is_active, True)
        product_id = stripe_product.pk
        url = f"/courses/{course.pk}/"
        response = self.client.put(
            url, {"name": "updated_course", "description": "updated_description", "usd_price": 11111}
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": course.pk,
                "name": "updated_course",
                "description": "updated_description",
                "owner": self.user.pk,
                "preview": None,
                "lessons_count": 2,
                "lessons_details": [
                    {
                        "id": 14,
                        "description": "description of lesson_14",
                        "link_to_video": "youtube.com/lesson_14",
                        "name": "lesson_14",
                        "preview": None,
                        "usd_price": 2000,
                        "course": 10,
                    },
                    {
                        "id": 15,
                        "description": "description of lesson_15",
                        "link_to_video": "youtube.com/lesson_15",
                        "name": "lesson_15",
                        "preview": None,
                        "usd_price": 1000,
                        "course": 10,
                    },
                ],
                "relation_status": "owner",
                "usd_price": 11111,
            },
        )
        self.assertEqual(len(StripeProduct.objects.all()), 26)
        self.assertEqual(len(StripeProduct.objects.filter(course=course)), 2)
        self.assertEqual(len(StripeProduct.objects.filter(course=course, is_active=True)), 1)
        old_product = StripeProduct.objects.get(pk=product_id)
        self.assertEqual(old_product.is_active, False)

    def test_course_partial_updating_by_moderator(self) -> None:
        """Тест запроса на изменение объекта модели Course модератором"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        course = Course.objects.get(name="course_4")
        self.user.groups.add(self.moderators)
        self.assertEqual(len(StripeProduct.objects.filter(course=course)), 1)
        stripe_product = StripeProduct.objects.get(course=course)
        self.assertEqual(stripe_product.is_active, True)
        product_id = stripe_product.pk
        url = f"/courses/{course.pk}/"
        response = self.client.patch(url, {"name": "updated_by_moderator"})
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": course.pk,
                "name": "updated_by_moderator",
                "description": "description of course_4",
                "owner": course.owner.pk,
                "preview": None,
                "lessons_count": 0,
                "lessons_details": [],
                "relation_status": "undefined",
                "usd_price": 77777,
            },
        )
        self.assertEqual(len(StripeProduct.objects.all()), 26)
        self.assertEqual(len(StripeProduct.objects.filter(course=course)), 2)
        self.assertEqual(len(StripeProduct.objects.filter(course=course, is_active=True)), 1)
        old_product = StripeProduct.objects.get(pk=product_id)
        self.assertEqual(old_product.is_active, False)

    def test_course_forbidden_destroy(self) -> None:
        """Тест неудачной попытки запроса на удаление объекта модели Course модератором"""

        course = Course.objects.get(name="course_3")
        self.user.groups.add(self.moderators)
        url = f"/courses/{course.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_destroy(self) -> None:
        """Тест успешного запроса на удаление объекта модели Course его владельцем"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        course = Course.objects.get(name="course_8")
        self.assertEqual(len(StripeProduct.objects.filter(course=course)), 1)
        stripe_product = StripeProduct.objects.get(course=course)
        product_id = stripe_product.pk
        url = f"/courses/{course.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(StripeProduct.objects.all()), 25)
        updated_stripe_product = StripeProduct.objects.get(pk=product_id)
        self.assertEqual(updated_stripe_product.product_name, "course_8")
        self.assertEqual(updated_stripe_product.product_type, "course")
        self.assertEqual(updated_stripe_product.course, None)


class LessonTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Lesson"""

    fixtures = ["course_fixture.json", "customuser_fixture.json", "lesson_fixture.json", "stripeproduct_fixture.json"]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.moderators = Group.objects.create(name="Модераторы")
        self.user = CustomUser.objects.get(email="user_3@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_lesson_creating(self) -> None:
        """Тест запроса на создание объекта модели Lesson"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        url = reverse("education:lesson_create")
        course = Course.objects.get(name="course_6")
        response = self.client.post(
            url,
            data={
                "name": "test_lesson",
                "description": "test_description",
                "link_to_video": "https://youtube.com/test_lesson",
                "course": course.pk,
                "usd_price": 999,
            },
        )
        data = response.json()
        lessons_count = Lesson.objects.count()
        self.assertEqual(lessons_count, 16)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data.get("course"), course.pk)
        self.assertEqual(data.get("name"), "test_lesson")
        self.assertEqual(len(StripeProduct.objects.all()), 26)
        stripe_product = StripeProduct.objects.get(lesson__name="test_lesson")
        self.assertEqual(stripe_product.course, None)
        self.assertEqual(stripe_product.is_active, True)
        self.assertEqual(stripe_product.owner_email, "user_3@mail.py")
        self.assertEqual(stripe_product.product_price, 999)

    def test_lesson_creating_by_moderator(self) -> None:
        """Тест попытки запроса на создание объекта модели Lesson модератором"""

        self.user.groups.add(self.moderators)
        url = reverse("education:lesson_create")
        course = Course.objects.get(name="course_6")
        response = self.client.post(
            url,
            data={
                "name": "test_lesson",
                "description": "test_description",
                "link_to_video": "https://youtube.com/test_lesson",
                "course": course.pk,
                "usd_price": 333,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_creating_not_for_own_course(self) -> None:
        """Тест попытки запроса на создание объекта модели Lesson для чужого курса"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        url = reverse("education:lesson_create")
        course = Course.objects.get(name="course_7")
        response = self.client.post(
            url,
            data={
                "name": "test_lesson",
                "description": "test_description",
                "link_to_video": "https://youtube.com/test_lesson",
                "course": course.pk,
                "usd_price": 888,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(StripeProduct.objects.all()), 25)

    def test_getting_lessons_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Lesson"""

        url = "/lessons/?ordering=id&page_size=12"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 10)
        self.assertEqual(data["count"], 15)
        prices_sum = 0
        for i in range(10):
            lesson = data["results"][i]
            description = lesson.get("description")
            link = lesson.get("link_to_video")
            if i not in [6, 7, 8]:
                self.assertEqual((description, link), (None, None))
            else:
                self.assertEqual(
                    (description, link), (f"description of lesson_{i + 1}", f"youtube.com/lesson_{i + 1}")
                )
            prices_sum += lesson["usd_price"]
        self.assertEqual(prices_sum, 105000)

    def test_lesson_retrieve_by_moderator(self) -> None:
        """Тест запроса на просмотр объекта модели Lesson пользователем-модератором"""

        self.user.groups.add(self.moderators)
        lesson = Lesson.objects.get(name="lesson_13")
        url = f"/lessons/{lesson.pk}/"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(
            data,
            {
                "id": lesson.pk,
                "name": "lesson_13",
                "description": "description of lesson_13",
                "preview": None,
                "link_to_video": "youtube.com/lesson_13",
                "course": lesson.course.pk,
                "usd_price": 3000,
            },
        )

    def test_lesson_forbidden_retrieve(self) -> None:
        """Тест запроса на отображение объекта модели Lesson пользователю, не имеющему права на просмотр"""

        lesson = Lesson.objects.get(name="lesson_11")
        url = f"/lessons/{lesson.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_updating_by_moderator(self) -> None:
        """Тест запроса на изменение объекта модели Lesson пользователем-модератором"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        self.user.groups.add(self.moderators)
        lesson = Lesson.objects.get(name="lesson_15")
        other_course = Course.objects.get(name="course_8")
        self.assertEqual(len(StripeProduct.objects.filter(lesson=lesson)), 1)
        stripe_product = StripeProduct.objects.get(lesson=lesson)
        product_id = stripe_product.pk
        self.assertEqual(stripe_product.is_active, True)
        url = f"/lessons/update/{lesson.pk}/"
        response = self.client.put(
            url,
            data={
                "name": "updated_lesson",
                "description": "updated_description",
                "link_to_video": "https://youtube.com/lesson_15",
                "course": other_course.pk,
                "usd_price": 888,
            },
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": lesson.pk,
                "name": "updated_lesson",
                "description": "updated_description",
                "preview": None,
                "link_to_video": "https://youtube.com/lesson_15",
                "course": other_course.pk,
                "usd_price": 888,
            },
        )
        self.assertEqual(len(StripeProduct.objects.all()), 26)
        self.assertEqual(len(StripeProduct.objects.filter(lesson=lesson)), 2)
        self.assertEqual(len(StripeProduct.objects.filter(lesson=lesson, is_active=True)), 1)
        old_product = StripeProduct.objects.get(pk=product_id)
        self.assertEqual(old_product.is_active, False)

    def test_lesson_forbidden_updating(self) -> None:
        """Тест попытки запроса на изменение объекта модели Lesson пользователем не имеющим прав"""

        lesson = Lesson.objects.get(name="lesson_15")
        other_course = Course.objects.get(name="course_8")
        url = f"/lessons/update/{lesson.pk}/"
        response = self.client.patch(url, data={"course": other_course.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_invalid_course_updating_by_owner(self) -> None:
        """Тест попытки запроса на присвоение объекта модели Lesson другому пользователю"""

        lesson = Lesson.objects.get(name="lesson_8")
        other_course = Course.objects.get(name="course_2")
        url = f"/lessons/update/{lesson.pk}/"
        response = self.client.patch(url, data={"course": other_course.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_invalid_course_updating_by_moderator(self) -> None:
        """Тест попытки запроса на присвоение объекта модели Lesson другому пользователю"""

        self.user.groups.add(self.moderators)
        lesson = Lesson.objects.get(name="lesson_3")
        other_course = Course.objects.get(name="course_5")
        url = f"/lessons/update/{lesson.pk}/"
        response = self.client.patch(url, data={"course": other_course.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_destroy(self) -> None:
        """Тест запроса на удаление объекта модели Lesson владельцем"""

        self.assertEqual(len(StripeProduct.objects.all()), 25)
        lesson = Lesson.objects.get(name="lesson_9")
        self.assertEqual(len(StripeProduct.objects.filter(lesson=lesson)), 1)
        stripe_product = StripeProduct.objects.get(lesson=lesson)
        product_id = stripe_product.pk
        url = f"/lessons/delete/{lesson.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(StripeProduct.objects.all()), 25)
        updated_stripe_product = StripeProduct.objects.get(pk=product_id)
        self.assertEqual(updated_stripe_product.product_name, "lesson_9")
        self.assertEqual(updated_stripe_product.product_type, "lesson")
        self.assertEqual(updated_stripe_product.lesson, None)

    def test_lesson_destroy_by_moderator(self) -> None:
        """Тест попытки запроса на удаление объекта модели Lesson модератором"""

        self.user.groups.add(self.moderators)
        lesson = Lesson.objects.get(name="lesson_14")
        url = f"/lessons/delete/{lesson.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PaymentTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Payment"""

    fixtures = [
        "course_fixture.json",
        "customuser_fixture.json",
        "lesson_fixture.json",
        "payment_fixture.json",
        "stripeproduct_fixture.json",
    ]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.user = CustomUser.objects.get(email="user_5@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_getting_courses_payments_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Payment с применением фильтрации"""

        course = Course.objects.get(name="course_9")
        url = f"/payments/?payment_category=courses&paid_course={course.pk}"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 2)
        total_sum = sum([payment["amount"] for payment in data["results"]])
        self.assertEqual(total_sum, 44444)

    def test_getting_lessons_payments_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Payment с применением фильтрации"""

        url = "/payments/?payment_category=lessons&method=cash"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 3)
        total_sum = sum([payment["amount"] for payment in data["results"]])
        self.assertEqual(total_sum, 13000)

    def test_other_getting_lessons_payments_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Payment с применением фильтрации"""

        url = "/payments/?paid_lesson=1&paid_course=33"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["amount"], 15000)


class StripeSessionSubscriptionTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов моделей StripeSession и Subscription"""

    fixtures = [
        "course_fixture.json",
        "customuser_fixture.json",
        "lesson_fixture.json",
        "stripeproduct_fixture.json",
        "stripesession_fixture.json",
        "subscription_fixture.json",
    ]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.user = CustomUser.objects.get(email="user_5@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_own_session_retrieve(self) -> None:
        """Тест запроса на просмотр собственной сессии"""

        session = StripeSession.objects.get(pk=1)
        url = f"/payment_success/?session_id={session.session_id}"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": 1,
                "session_id": "cs_test_a1Nks8Tc82jfQ71knHenRlmEh1gfJGePOrQ0oSFejoZBUecP4hKTquyAAy",
                "session_url": "https://checkout.stripe.com/c/pay/cs_test_endless_link_001",
                "customer": 5,
                "product": {
                    "product_type": "course",
                    "product_id": 10,
                    "product_name": "course_10",
                    "product_price": 11111,
                },
                "status": "complete",
            },
        )

    def test_session_status_auto_updating(self) -> None:
        """Тест запроса на просмотр собственной сессии с истекшим сроком годности"""

        session = StripeSession.objects.get(pk=2)
        url = f"/payment_success/?session_id={session.session_id}"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": 2,
                "session_id": "cs_test_a12XCQTC6otGUIw17j5obwjYlWjW03pqrOmfr5Iji3UGHXHmYnxa521lZG",
                "session_url": "https://checkout.stripe.com/c/pay/cs_test_endless_link_002",
                "customer": 5,
                "product": {
                    "product_type": "course",
                    "product_id": 9,
                    "product_name": "course_9",
                    "product_price": 22222,
                },
                "status": "expired",
            },
        )

    def test_session_forbidden(self) -> None:
        """Тест запроса на просмотр чужой сессии"""

        session = StripeSession.objects.get(pk=3)
        url = f"/payment_success/?session_id={session.session_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_invalid_id(self) -> None:
        """Тест запроса без параметра session_id"""

        url = "/payment_success/?pk=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Параметр session_id не указан в url."})

    def test_session_opening(self) -> None:
        """Тест запроса на открытие сессии для оплаты подписки на курс"""

        self.assertEqual(len(StripeSession.objects.all()), 3)
        course = Course.objects.get(name="course_2")
        url = f"/courses/{course.pk}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(len(StripeSession.objects.all()), 4)
        new_session = StripeSession.objects.get(product__course=course)
        link_start = data["session_url"][:34]
        self.assertEqual(link_start, "https://checkout.stripe.com/c/pay/")
        self.assertEqual(new_session.session_url, data["session_url"])

    def test_subscription_own_course_activating(self) -> None:
        """Тест попытки запроса на получение пользователем подписки на собственный курс"""

        self.assertEqual(len(StripeSession.objects.all()), 3)
        user = CustomUser.objects.get(email="user_1@mail.py")
        self.client.force_authenticate(user=user)
        course = Course.objects.get(name="course_1")
        url = f"/courses/{course.pk}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Запрещено подписываться на собственный курс."})
        self.assertEqual(len(StripeSession.objects.all()), 3)

    def test_subscription_repeat_course_activating(self) -> None:
        """Тест попытки запроса на повторное получение пользователем уже имеющейся подписки на курс"""

        self.assertEqual(len(StripeSession.objects.all()), 3)
        course = Course.objects.get(name="course_10")
        url = f"/courses/{course.pk}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Вы уже подписаны на данный курс."})
        self.assertEqual(len(StripeSession.objects.all()), 3)

    def test_subscription_deactivating(self) -> None:
        """Тест запроса на отказ пользователя от подписки на курс"""

        self.assertEqual(len(Subscription.objects.all()), 2)
        course = Course.objects.get(name="course_10")
        url = f"/courses/{course.pk}/refuse/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Подписка отключена."})
        self.assertEqual(len(Subscription.objects.all()), 1)

    def test_not_existing_subscription_deactivating(self) -> None:
        """Тест попытки запроса на отказ пользователя от несуществующей подписки на курс"""

        course = Course.objects.get(name="course_6")
        url = f"/courses/{course.pk}/refuse/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WebhookTestCase(APITestCase):
    """Группа тестов для контроллера обработки вебхуков"""

    fixtures = [
        "course_fixture.json",
        "customuser_fixture.json",
        "lesson_fixture.json",
        "payment_fixture.json",
        "stripeproduct_fixture.json",
        "stripesession_fixture.json",
        "subscription_fixture.json",
    ]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.user = CustomUser.objects.get(email="user_5@mail.py")
        self.client.force_authenticate(user=self.user)
        self.payload = {
            "id": "evt_test_event_id",
            "type": "checkout.session.completed",
            "created": 1783657036,
            "data": {
                "object": {
                    "id": "cs_test_a12XCQTC6otGUIw17j5obwjYlWjW03pqrOmfr5Iji3UGHXHmYnxa521lZG",
                    "status": "complete",
                    "amount_total": 22222,
                    "currency": "usd",
                    "mode": "payment",
                    "client_reference_id": "5",
                    "metadata": {
                        "product_type": "course",
                        "product_id": "9",
                    },
                }
            },
        }

    @patch("stripe.Webhook.construct_event")
    def test_subscription_activating(self, mock_construct_event: Any) -> None:
        """Тест активации подписки после совершения пользователем платежа"""

        mock_event = Event.construct_from(self.payload, None)
        mock_construct_event.return_value = mock_event

        self.assertEqual(len(Payment.objects.all()), 10)
        self.assertEqual(Subscription.objects.filter(subscriber=self.user, course__pk=9).exists(), False)
        self.assertEqual(len(StripeSession.objects.all()), 3)
        session = StripeSession.objects.get(
            session_id="cs_test_a12XCQTC6otGUIw17j5obwjYlWjW03pqrOmfr5Iji3UGHXHmYnxa521lZG"
        )
        self.assertEqual(session.status, "open")
        response = self.client.post(
            "/webhook/",
            data=json.dumps(self.payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test_signature",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(StripeSession.objects.all()), 3)
        updated_session = StripeSession.objects.get(
            session_id="cs_test_a12XCQTC6otGUIw17j5obwjYlWjW03pqrOmfr5Iji3UGHXHmYnxa521lZG"
        )
        self.assertEqual(updated_session.status, "complete")
        self.assertEqual(len(Payment.objects.all()), 11)
        new_payment = Payment.objects.get(created_at="2026-07-10 04:17:16+00:00")
        self.assertEqual(new_payment.amount, 22222)
        self.assertEqual(new_payment.payer, self.user)
        self.assertEqual(new_payment.method, "cashless")
        self.assertEqual(Subscription.objects.filter(subscriber=self.user, course__pk=9).exists(), True)

    @patch("stripe.Webhook.construct_event")
    def test_session_expired(self, mock_construct_event: Any) -> None:
        """Тест смены статуса сессии на "expired" """

        expired_payload = self.payload
        expired_payload["type"] = "checkout.session.expired"
        expired_payload["data"]["object"]["status"] = "expired"  # type: ignore
        mock_event = Event.construct_from(expired_payload, None)
        mock_construct_event.return_value = mock_event

        self.assertEqual(len(Payment.objects.all()), 10)
        self.assertEqual(Subscription.objects.filter(subscriber=self.user, course__pk=9).exists(), False)
        self.assertEqual(len(StripeSession.objects.all()), 3)
        session = StripeSession.objects.get(
            session_id="cs_test_a12XCQTC6otGUIw17j5obwjYlWjW03pqrOmfr5Iji3UGHXHmYnxa521lZG"
        )
        self.assertEqual(session.status, "open")
        response = self.client.post(
            "/webhook/",
            data=json.dumps(expired_payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test_signature",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(StripeSession.objects.all()), 3)
        updated_session = StripeSession.objects.get(
            session_id="cs_test_a12XCQTC6otGUIw17j5obwjYlWjW03pqrOmfr5Iji3UGHXHmYnxa521lZG"
        )
        self.assertEqual(updated_session.status, "expired")
        self.assertEqual(len(Payment.objects.all()), 10)
        self.assertEqual(Subscription.objects.filter(subscriber=self.user, course__pk=9).exists(), False)

    def test_not_stripe_request(self) -> None:
        """Тест запроса с невалидной Stripe-подписью"""

        response = self.client.post(
            "/webhook/",
            data=json.dumps(self.payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test_signature",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Невалидная Stripe-подпись."})
