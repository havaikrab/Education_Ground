from rest_framework import serializers

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

    class Meta:
        """Параметры сериализатора"""

        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "phone", "city", "avatar")
