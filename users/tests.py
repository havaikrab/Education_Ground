from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser


class CustomUserSpecialTestCase(APITestCase):
    """Тест процессов регистрации и авторизации пользователя"""

    def setUp(self) -> None:
        """Наполнение БД тестовыми данными"""

        pass

    def test_customuser_register(self) -> None:
        """Тест процессов регистрации и авторизации пользователя"""

        list_users_url = "/users/"
        unauthorized_response = self.client.get(list_users_url)
        self.assertEqual(unauthorized_response.status_code, status.HTTP_401_UNAUTHORIZED)

        register_url = "/users/register/"
        register_response = self.client.post(
            register_url,
            data={
                "username": "test_user",
                "email": "test@user.py",
                "first_name": "first_name",
                "last_name": "last_name",
                "password": "unusual_123",
                "password_confirm": "unusual_123",
            },
        )
        data = register_response.json()
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            data,
            {
                "username": "test_user",
                "email": "test@user.py",
                "first_name": "first_name",
                "last_name": "last_name",
                "phone": None,
                "city": None,
                "avatar": None,
            },
        )

        login_url = "/users/login/"
        login_response = self.client.post(login_url, data={"email": "test@user.py", "password": "unusual_123"})
        user_access_token = login_response.data.get("access")

        authorized_response = self.client.get(list_users_url, headers={"Authorization": f"Bearer {user_access_token}"})
        self.assertEqual(authorized_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            authorized_response.data,
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "username": "test_user",
                        "email": "test@user.py",
                        "first_name": "first_name",
                        "last_name": "last_name",
                        "phone": None,
                        "city": None,
                        "avatar": None,
                        "payments": [],
                        "subscriptions": [],
                    }
                ],
            },
        )

    def test_customuser_register_invalid_password(self) -> None:
        """Тест запроса на регистрацию нового пользователя с некорректным подтверждением пароля"""

        url = "/users/register/"
        response = self.client.post(
            url,
            data={
                "username": "test_user",
                "email": "test@user.py",
                "first_name": "first_name",
                "last_name": "last_name",
                "password": "unusual_123",
                "password_confirm": "unusual-123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomUserTestCase(APITestCase):
    """Группа тестов связанных с обработкой объектов модели CustomUser"""

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

        self.moderators = Group.objects.create(name="Модераторы")
        self.user = CustomUser.objects.get(email="user_5@mail.py")
        self.user.set_password("password")
        self.client.force_authenticate(user=self.user)

    def test_getting_users_list(self) -> None:
        """Тест запроса на получение списка всех зарегистрированных пользователей"""

        url = "/users/"
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 5)
        for user in data["results"]:
            if user["email"] == "user_5@mail.py":
                self.assertEqual(len(user["payments"]), 4)
                total_sum = sum([payment["amount"] for payment in user["payments"]])
                self.assertEqual(total_sum, 46333)
                self.assertEqual(
                    user["subscriptions"],
                    [
                        {
                            "course": 10,
                            "course_name": "course_10",
                            "course_preview": None,
                            "payment_status": True,
                            "payment_amount": 21111,
                        }
                    ],
                )
            else:
                not_exists = [user.get("last_name", True), user.get("payments", True), user.get("subscriptions", True)]
                self.assertEqual(not_exists, [True, True, True])

    def test_user_wrong_creating(self) -> None:
        """Тест попытки запроса на создание объекты модели CustomUser неправильным способом"""

        url = "/users/"
        response = self.client.post(
            url,
            data={
                "username": "test_user",
                "email": "test@user.py",
                "first_name": "first_name",
                "last_name": "last_name",
                "password": "unusual_123",
                "password_confirm": "unusual_123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_updating(self) -> None:
        """Тест запроса на изменение данных пользователя"""

        url = f"/users/{self.user.pk}/"
        response = self.client.patch(url, data={"phone": "новый телефон"})
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["phone"], "новый телефон")

    def test_user_forbidden_updating(self) -> None:
        """Тест попытки запроса на изменение чужих данных пользователя"""

        other_user = CustomUser.objects.get(username="user_1")
        url = f"/users/{other_user.pk}/"
        response = self.client.patch(url, data={"phone": "новый телефон"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete(self) -> None:
        """Тест запроса на удаление аккаунта пользователя"""

        user_pk = self.user.pk
        url = f"/users/{user_pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        repeat_url = f"/users/{user_pk}/"
        repeat_response = self.client.get(repeat_url)
        self.assertEqual(repeat_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_forbidden_delete(self) -> None:
        """Тест попытки запроса на удаление чужого аккаунта пользователя"""

        other_user = CustomUser.objects.get(username="user_1")
        url = f"/users/{other_user.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_change_password(self) -> None:
        """Тест запроса на смену пароля от аккаунта"""

        old_hashed_password = self.user.password
        url = "/users/change_password/"
        response = self.client.post(
            url,
            data={
                "current_password": "password",
                "new_password": "new_password",
                "new_password_confirm": "new_password",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(old_hashed_password == self.user.password, False)

    def test_user_change_password_invalid_confirm(self) -> None:
        """Тест попытки запроса на смену пароля от аккаунта с неудачным подтверждением нового пароля"""

        url = "/users/change_password/"
        response = self.client.post(
            url,
            data={
                "current_password": "password",
                "new_password": "new_password",
                "new_password_confirm": "new-password",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_change_password_invalid_current(self) -> None:
        """Тест попытки запроса на смену пароля от аккаунта с некорректным вводом действующего пароля"""

        url = "/users/change_password/"
        response = self.client.post(
            url,
            data={
                "current_password": "PASSWORD",
                "new_password": "new_password",
                "new_password_confirm": "new_password",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_getting_course_with_subscription_list(self) -> None:
        """Тест запроса на отображение пользователю списка объектов модели Course c оплаченной подпиской"""

        url = "/courses/?subscription=True&ordering=id&paid=True"
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["next"], None)
        for result in data["results"]:
            self.assertEqual(result["relation_status"], "subscriber")
