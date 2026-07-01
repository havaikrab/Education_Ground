from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from config import test_data
from education.models import Course
from users.models import CustomUser


class CourseTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Course"""

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        test_data.set_courses_data()
        self.moderators = Group.objects.create(name="Модераторы")
        self.user = CustomUser.objects.get(email="user_4@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_course_creating(self) -> None:
        """Тест запроса на создание объекта модели Course"""

        url = reverse("education:course-list")
        response = self.client.post(
            url, data={"name": "test_course", "description": "test_description with valid link https://youtube.com"}
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
        random_pk = random_user.pk
        url = f"/courses/?owner={random_pk}"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 3)
        names = set()
        for result in data["results"]:
            self.assertEqual(result["relation_status"], "undefined")
            self.assertEqual(len(result), 5)
            names.add(result["name"])
        self.assertEqual(names, {"course_4", "course_5", "course_6"})

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
            },
        )

    def test_course_updating(self) -> None:
        """Тест запроса на изменение объекта модели Course владельцем"""

        course = Course.objects.get(name="course_10")
        url = f"/courses/{course.pk}/"
        response = self.client.put(url, {"name": "updated_course", "description": "updated_description"})
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
