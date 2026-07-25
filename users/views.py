from typing import Any

from django.utils.decorators import method_decorator
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from education.paginators import EducationPaginator

from .models import CustomUser
from .permissions import IsOwner
from .serializers import CustomUserChangePasswordSerializer, CustomUserRegisterSerializer, CustomUserSerializer


@method_decorator(
    name="post",
    decorator=extend_schema(
        summary="Регистрация нового пользователя",
        responses={
            200: OpenApiResponse(description="""
{"username": "test_user", "email": "test@user.py", "first_name": "Test", "last_name": "User",
"phone": null, "city": null, "avatar": null}
"""),
            400: OpenApiResponse(description="""
- Не указано одно или несколько обязательных полей:
  "username", "email", "first_name", "last_name", "password", "password_confirm".
- Пароли не совпадают.
- Пользователь с таким "username" или "email" уже существует.
"""),
        },
    ),
)
class CustomUserRegisterAPIView(CreateAPIView):
    """Контроллер регистрации нового пользователя"""

    serializer_class = CustomUserRegisterSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    create=extend_schema(
        summary="Метод не поддерживается",
        description="""
Для создания новой учетной записи используется адрес /users/register/
- Неавторизованный пользователь получит сообщение о необходимости авторизоваться.
- Авторизованному пользователю будет возвращена ошибка со статусом 405 - метод не поддерживается
""",
    ),
    list=extend_schema(
        summary="Отображение списка аккаунтов с пагинацией и фильтрацией",
        description="""
Необходима авторизация.
Авторизованному пользователю отображается вся собственная личная информация и список аккаунтов других пользователей
со скрытыми полями "last_name", "payments", "subscriptions".
""",
    ),
    retrieve=extend_schema(
        summary="Отображение деталей аккаунта",
        description="""
Необходима авторизация.
Авторизованному пользователю в собственном профиле отображается вся личная информация
в чужом профиле скрыты поля "last_name", "payments", "subscriptions".
""",
    ),
    update=extend_schema(
        summary="Полное обновление аккаунта пользователя",
        description="""
Необходима авторизация и права владельца.
В теле запроса необходимо передать обязательные ключи "username", "email", "first_name" и "last_name"
с соответствующими значениями.
""",
    ),
    partial_update=extend_schema(
        summary="Частичное обновление аккаунта пользователя",
        description="""
Необходима авторизация и права владельца.
В теле запроса нужно указать новые значения для одного или нескольких полей "username", "email", "first_name",
"last_name", "phone", "city", "avatar".
""",
    ),
    destroy=extend_schema(
        summary="Удаление аккаунта пользователя со всеми собственными курсами, уроками, подписками и платежами.",
        description="Необходима авторизация и права владельца.",
    ),
)
class CustomUserViewSet(ModelViewSet):
    """Вьюсет для модели пользователя"""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    http_method_names = ["get", "put", "patch", "delete"]
    pagination_class = EducationPaginator
    ordering_fields = ["id", "email"]
    search_fields = ["email"]

    def get_permissions(self) -> list:
        """Указание необходимых разрешений для соответствующих действий контроллера"""

        if self.action in ["destroy", "update", "partial_update"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


@method_decorator(
    name="post",
    decorator=extend_schema(
        summary="Смена пароля от аккаунта",
        responses={
            204: OpenApiResponse(description='При удачной смене возвращается "пустой" объект response.'),
            400: OpenApiResponse(description="""
- Неверный текущий пароль.
- Новый пароль не подтвержден.
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
        },
    ),
)
class CustomUserChangePasswordAPIView(APIView):
    """Контроллер обновления пароля от аккаунта"""

    serializer_class = CustomUserChangePasswordSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST-запрос на смену пароля"""

        serializer = CustomUserChangePasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
