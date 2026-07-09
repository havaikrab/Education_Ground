from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from config import test_data
from education.models import Course, Lesson
from users.models import CustomUser


class CourseTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Course"""

    fixtures = ["course_fixture.json", "customuser_fixture.json"]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.moderators = Group.objects.create(name="Модераторы")
        self.user = CustomUser.objects.get(email="user_4@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_course_creating(self) -> None:
        """Тест запроса на создание объекта модели Course"""

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
                "lessons_count": 0,
                "lessons_details": [],
                "relation_status": "undefined",
                "usd_price": 111111,
            },
        )

    def test_course_updating(self) -> None:
        """Тест запроса на изменение объекта модели Course владельцем"""

        course = Course.objects.get(name="course_10")
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
                "lessons_count": 0,
                "lessons_details": [],
                "relation_status": "owner",
                "usd_price": 11111,
            },
        )

    def test_course_partial_updating_by_moderator(self) -> None:
        """Тест запроса на изменение объекта модели Course модератором"""

        course = Course.objects.get(name="course_3")
        self.user.groups.add(self.moderators)
        url = f"/courses/{course.pk}/"
        response = self.client.patch(url, {"name": "updated_by_moderator"})
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data,
            {
                "id": course.pk,
                "name": "updated_by_moderator",
                "description": "description of course_3",
                "owner": course.owner.pk,
                "preview": None,
                "lessons_count": 0,
                "lessons_details": [],
                "relation_status": "undefined",
                "usd_price": 88888,
            },
        )

    def test_course_forbidden_destroy(self) -> None:
        """Тест неудачной попытки запроса на удаление объекта модели Course модератором"""

        course = Course.objects.get(name="course_3")
        self.user.groups.add(self.moderators)
        url = f"/courses/{course.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_destroy(self) -> None:
        """Тест успешного запроса на удаление объекта модели Course его владельцем"""

        course = Course.objects.get(name="course_8")
        url = f"/courses/{course.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class LessonTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Lesson"""

    fixtures = ["course_fixture.json", "customuser_fixture.json", "lesson_fixture.json"]

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        self.moderators = Group.objects.create(name="Модераторы")
        self.user = CustomUser.objects.get(email="user_3@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_lesson_creating(self) -> None:
        """Тест запроса на создание объекта модели Lesson"""

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

        self.user.groups.add(self.moderators)
        lesson = Lesson.objects.get(name="lesson_15")
        other_course = Course.objects.get(name="course_8")
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

        lesson = Lesson.objects.get(name="lesson_9")
        url = f"/lessons/delete/{lesson.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_lesson_destroy_by_moderator(self) -> None:
        """Тест попытки запроса на удаление объекта модели Lesson модератором"""

        self.user.groups.add(self.moderators)
        lesson = Lesson.objects.get(name="lesson_14")
        url = f"/lessons/delete/{lesson.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PaymentTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Payment"""

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        test_data.set_payments_data()
        self.user = CustomUser.objects.get(email="user_5@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_getting_courses_payments_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Payment с применением фильтрации"""

        course = Course.objects.get(name="course_9")
        url = f"/payments/?payment_category=courses&paid_course={course.pk}"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 2)
        total_sum = sum([payment["amount"] for payment in data])
        self.assertEqual(total_sum, 2200)

    def test_getting_lessons_payments_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Payment с применением фильтрации"""

        url = "/payments/?payment_category=lessons&method=cash"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)
        total_sum = sum([payment["amount"] for payment in data])
        self.assertEqual(total_sum, 800)


class SubscriptionTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Subscription"""

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        test_data.set_subscriptions_data()
        self.user = CustomUser.objects.get(email="user_1@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_subscription_activating(self) -> None:
        """Тест запроса на получение пользователем подписки на курс"""

        url = f"/users/{self.user.pk}/"

        response = self.client.get(url)
        data = response.json()
        subscriptions = set()
        for subscription in data["subscriptions"]:
            subscriptions.add(subscription["course_name"])
        self.assertEqual(subscriptions, {"course_8", "course_9", "course_10"})

        course = Course.objects.get(name="course_7")
        activating_url = f"/courses/{course.pk}/subscribe/"
        activating_response = self.client.post(activating_url)
        self.assertEqual(activating_response.status_code, status.HTTP_200_OK)
        self.assertEqual(activating_response.data, {"message": "Подписка оформлена"})

        result_response = self.client.get(url)
        result_data = result_response.json()
        result_subscriptions = set()
        for subscription in result_data["subscriptions"]:
            result_subscriptions.add(subscription["course_name"])
        self.assertEqual(result_subscriptions, {"course_7", "course_8", "course_9", "course_10"})

    def test_subscription_own_course_activating(self) -> None:
        """Тест попытки запроса на получение пользователем подписки на собственный курс"""

        course = Course.objects.get(name="course_1")
        url = f"/courses/{course.pk}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Запрещено подписываться на собственный курс."})

    def test_subscription_repeat_course_activating(self) -> None:
        """Тест попытки запроса на повторное получение пользователем уже имеющейся подписки на курс"""

        course = Course.objects.get(name="course_10")
        url = f"/courses/{course.pk}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Вы уже подписаны на данный курс."})

    def test_subscription_deactivating(self) -> None:
        """Тест запроса на отказ пользователя от подписки на курс"""

        url = f"/users/{self.user.pk}/"

        response = self.client.get(url)
        data = response.json()
        subscriptions = set()
        for subscription in data["subscriptions"]:
            subscriptions.add(subscription["course_name"])
        self.assertEqual(subscriptions, {"course_8", "course_9", "course_10"})

        course = Course.objects.get(name="course_9")
        deactivating_url = f"/courses/{course.pk}/refuse/"
        deactivating_response = self.client.delete(deactivating_url)
        self.assertEqual(deactivating_response.status_code, status.HTTP_200_OK)
        self.assertEqual(deactivating_response.data, {"message": "Подписка отключена."})

        result_response = self.client.get(url)
        result_data = result_response.json()
        result_subscriptions = set()
        for subscription in result_data["subscriptions"]:
            result_subscriptions.add(subscription["course_name"])
        self.assertEqual(result_subscriptions, {"course_8", "course_10"})

    def test_not_existing_subscription_deactivating(self) -> None:
        """Тест попытки запроса на отказ пользователя от несуществующей подписки на курс"""

        course = Course.objects.get(name="course_6")
        url = f"/courses/{course.pk}/refuse/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
