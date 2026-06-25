from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from users.models import CustomUser


class Course(models.Model):
    """Модель курса"""

    name: models.CharField = models.CharField(max_length=200, verbose_name="Название курса")
    preview: models.ImageField = models.ImageField(
        upload_to="courses_previews", verbose_name="Превью курса", blank=True, null=True
    )
    description: models.TextField = models.TextField(verbose_name="Описание курса")
    owner: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Владелец",
        null=True,
        blank=False,
    )

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["name"]

    def __str__(self) -> str:
        """Строковое отображение объекта курса"""

        return str(self.name)


class Lesson(models.Model):
    """Модель урока"""

    name: models.CharField = models.CharField(max_length=200, verbose_name="Название урока")
    description: models.TextField = models.TextField(verbose_name="Описание урока")
    preview: models.ImageField = models.ImageField(
        upload_to="lessons_previews", verbose_name="Превью урока", blank=True, null=True
    )
    link_to_video: models.URLField = models.URLField(verbose_name="Ссылка на видео", blank=True, null=True)
    course: models.ForeignKey = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс"
    )

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["name"]

    def __str__(self) -> str:
        """Строковое отображение объекта урока"""

        return str(self.name)


class Payment(models.Model):
    """Модель платежа"""

    payer: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="payments", verbose_name="Плательщик"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата платежа")
    paid_course: models.ForeignKey = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_payments",
        verbose_name="Оплаченный курс",
        null=True,
        blank=True,
    )
    paid_lesson: models.ForeignKey = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="lesson_payments",
        verbose_name="Оплаченный урок",
        null=True,
        blank=True,
    )
    amount: models.PositiveIntegerField = models.PositiveIntegerField(verbose_name="Сумма платежа")
    METHOD_CHOICES = [("cash", "Наличными"), ("cashless", "Перевод")]
    method: models.CharField = models.CharField(max_length=8, choices=METHOD_CHOICES, verbose_name="Способ оплаты")

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Строковое отображение объекта платежа"""

        return f"{self.amount} {self.method}"

    def clean_method(self) -> str:
        """Проверяет способ платежа"""

        valid_methods = [method[0] for method in self.METHOD_CHOICES]
        if self.method not in valid_methods or not isinstance(self.method, str):
            raise ValidationError("Неизвестный способ оплаты")
        return self.method

    def clean(self) -> None:
        """Проверяет указание назначения платежа"""

        if self.paid_course and self.paid_lesson:
            raise ValidationError("Платеж может быть совершен только за один курс или один урок")
        if not self.paid_course and not self.paid_lesson:
            raise ValidationError("Не указано назначение платежа")
        super().clean()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Проверка валидности данных перед сохранением объекта в БД"""
        self.full_clean()
        super().save(*args, **kwargs)
