from django.urls import path
from rest_framework.routers import DefaultRouter

from .apps import UsersConfig
from .views import CustomUserRegisterAPIView, CustomUserViewSet

app_name = UsersConfig.name

router = DefaultRouter()
router.register("", CustomUserViewSet)

urlpatterns: list = [path("register/", CustomUserRegisterAPIView.as_view(), name="register")]

urlpatterns += router.urls
