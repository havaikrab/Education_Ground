from typing import Any

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


class CustomUserRegisterAPIView(CreateAPIView):
    """Контроллер регистрации нового пользователя"""

    serializer_class = CustomUserRegisterSerializer
    permission_classes = [AllowAny]


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


class CustomUserChangePasswordAPIView(APIView):
    """Контроллер обновления пароля от аккаунта"""

    serializer_class = CustomUserChangePasswordSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST-запрос на смену пароля"""

        serializer = CustomUserChangePasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
