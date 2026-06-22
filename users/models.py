from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Модель пользователя"""

    email = models.EmailField(unique=True, blank=False, null=False, verbose_name="Адрес электронной почты")
    first_name = models.CharField(blank=False, null=False, max_length=150, verbose_name="Имя")
    last_name = models.CharField(blank=False, null=False, max_length=150, verbose_name="Фамилия")
    phone: models.CharField = models.CharField(blank=True, null=True, max_length=15, verbose_name="Телефон")
    city: models.CharField = models.CharField(blank=True, null=True, max_length=150, verbose_name="Город")
    avatar: models.ImageField = models.ImageField(upload_to="avatars", blank=True, null=True, verbose_name="Аватар")

    class Meta:
        """Настройки отображения"""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        """Строковое представление пользователя"""

        return f"{self.email}"
