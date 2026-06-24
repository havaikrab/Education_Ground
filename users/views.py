from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import CustomUser
from .serializers import CustomUserRegisterSerializer, CustomUserSerializer


class CustomUserRegisterAPIView(CreateAPIView):
    """Контроллер регистрации нового пользователя"""

    serializer_class = CustomUserRegisterSerializer
    permission_classes = [AllowAny]


class CustomUserViewSet(ModelViewSet):
    """Вьюсет для модели пользователя"""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    http_method_names = ["get", "put", "patch", "delete"]
