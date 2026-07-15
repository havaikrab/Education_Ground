from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .apps import UsersConfig
from .serializers import AdvancedTokenObtainPairSerializer
from .views import CustomUserChangePasswordAPIView, CustomUserRegisterAPIView, CustomUserViewSet

app_name = UsersConfig.name

router = DefaultRouter()
router.register("", CustomUserViewSet)

urlpatterns: list = [
    path("register/", CustomUserRegisterAPIView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(serializer_class=AdvancedTokenObtainPairSerializer), name="login"),
    path("token_refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("change_password/", CustomUserChangePasswordAPIView.as_view(), name="change_password"),
]
urlpatterns += router.urls
