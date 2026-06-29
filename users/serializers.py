from typing import Any

from rest_framework import serializers

from education.serializers import PaymentSerializer

from .models import CustomUser


class CustomUserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор данных для регистрации нового пользователя"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        """Параметры сериализатора"""

        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "password",
            "password_confirm",
        )

    def validate(self, attrs: dict) -> dict:
        """Проверка совпадения передаваемых значений password_1 и password_2"""

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs

    def create(self, validated_data: dict) -> CustomUser:
        """Создание объекта пользователя с хешированием пароля"""

        validated_data.pop("password_confirm")
        user = CustomUser(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя"""

    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        """Параметры сериализатора"""

        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "phone", "city", "avatar", "payments")

    def to_representation(self, instance: CustomUser) -> dict:

        data = super().to_representation(instance)
        user = self.context["request"].user
        if instance != user:
            data.pop("last_name")
            data.pop("payments")
        return data


class CustomUserChangePasswordSerializer(serializers.ModelSerializer):
    """Сериализатор обновления пароля от аккаунта"""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        """Параметры сериализатора"""

        model = CustomUser
        fields = ("current_password", "new_password", "new_password_confirm")

    def validate_current_password(self, value: str) -> str:
        """Проверка, знает ли пользователь текущий пароль"""

        user = self.context.get("user")
        if not isinstance(user, CustomUser) or not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return value

    def validate(self, attrs: dict) -> dict:
        """Проверка совпадения передаваемых значений new_password и new_password_confirm"""

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs

    def save(self, **kwargs: Any) -> CustomUser:
        """Сохранение нового пароля"""

        user: CustomUser = self.context["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
