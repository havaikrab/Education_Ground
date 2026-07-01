from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from config import test_data
from users.models import CustomUser


class CourseTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели Course"""

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        test_data.set_courses_data()
        self.user = CustomUser.objects.get(email="user_1@mail.py")
        self.client.force_authenticate(user=self.user)

    def test_course_creating(self) -> None:
        """Тест запроса на создание объекта модели Course"""

        url = reverse("education:course-list")
        response = self.client.post(
            url, data={"name": "test_course", "description": "test_description of test_course"}
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data.get("owner"), self.user.pk)
        self.assertEqual(data.get("name"), "test_course")

    def test_getting_course_list(self) -> None:
        """Тест запроса на отображение списка объектов модели Course"""

        url = reverse("education:course-list")
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 5)
        # self.assertEqual(data.get("name"), "test_course")
