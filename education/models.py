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
    usd_price: models.PositiveIntegerField = models.PositiveIntegerField(
        verbose_name="Стоимость подписки на курс в центах USD"
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
    usd_price: models.PositiveIntegerField = models.PositiveIntegerField(
        verbose_name="Стоимость отдельного урока в центах USD"
    )

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["name"]

    def __str__(self) -> str:
        """Строковое отображение объекта урока"""

        return str(self.name)


class StripeProduct(models.Model):
    """Модель Stripe-идентификатора продукта"""

    course: models.ForeignKey = models.ForeignKey(
        Course, on_delete=models.SET_NULL, related_name="stripe_courses", verbose_name="Курс", blank=True, null=True
    )
    lesson: models.ForeignKey = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, related_name="stripe_lessons", verbose_name="Урок", blank=True, null=True
    )
    stripe_product_id: models.CharField = models.CharField(
        unique=True, max_length=255, verbose_name="id продукта в Stripe"
    )
    stripe_price_id: models.CharField = models.CharField(max_length=255, verbose_name="id цены в Stripe")
    is_active: models.BooleanField = models.BooleanField(default=True, verbose_name="Статус актуальности")
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    PRODUCT_TYPE_CHOICES = [("course", "Курс"), ("lesson", "Урок")]
    product_type: models.CharField = models.CharField(
        max_length=6, choices=PRODUCT_TYPE_CHOICES, verbose_name="Тип продукта"
    )
    product_name: models.CharField = models.CharField(max_length=200, verbose_name="Название продукта")
    product_price: models.PositiveIntegerField = models.PositiveIntegerField(verbose_name="Цена продукта")
    owner_id: models.PositiveIntegerField = models.PositiveIntegerField(verbose_name="id пользователя-владельца")
    owner_email: models.EmailField = models.EmailField(verbose_name="Адрес электронной почты владельца")

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Stripe-идентификатор"
        verbose_name_plural = "Stripe-идентификаторы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Строковое отображение Stripe-продукта"""

        return str(self.stripe_product_id)

    def clean(self) -> None:
        """Проверяет указание объекта идентификации"""

        if self.course and self.lesson:
            raise ValidationError("Идентификатор может ссылаться только на один объект урока или курса")
        if not self.course and not self.lesson:
            raise ValidationError("Не указан объект для идентификации")
        super().clean()

    def __fill_snapshot_data(self) -> None:
        """Заполняет денормализованные поля продукта"""

        if self.course:
            self.product_type = "course"
            self.product_name = self.course.name
            self.product_price = self.course.usd_price
            self.owner_id = self.course.owner.pk
            self.owner_email = self.course.owner.email
            old_products = StripeProduct.objects.filter(course=self.course)
        elif self.lesson:
            self.product_type = "lesson"
            self.product_name = self.lesson.name
            self.product_price = self.lesson.usd_price
            self.owner_id = self.lesson.course.owner.pk
            self.owner_email = self.lesson.course.owner.email
            old_products = StripeProduct.objects.filter(lesson=self.lesson)
        else:
            raise ValidationError("Не указаны обязательные данные для описания продукта")
        old_products.update(is_active=False)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Сохранение продукта с денормализованными данными"""

        self.__fill_snapshot_data()
        self.full_clean()
        super().save(*args, **kwargs)


class StripeSession(models.Model):
    """Модель Stripe-сессии"""

    session_id: models.CharField = models.CharField(unique=True, max_length=255, verbose_name="Идентификатор сессии")
    session_url: models.URLField = models.URLField(max_length=400, verbose_name="Ссылка на оплату")
    customer: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sessions", verbose_name="Заказчик"
    )
    product: models.ForeignKey = models.ForeignKey(
        StripeProduct, on_delete=models.CASCADE, related_name="stripe_sessions", verbose_name="Продукт"
    )
    STATUS_CHOICES = [("open", "Открыта"), ("complete", "Завершена"), ("expired", "Просрочена")]
    status: models.CharField = models.CharField(max_length=8, choices=STATUS_CHOICES, verbose_name="Статус сессии")

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Stripe-сессия"
        verbose_name_plural = "Stripe-сессии"
        ordering = ["-status"]

    def __str__(self) -> str:
        """Строковое отображение Stripe-сессии"""

        return str(self.session_id)


class Payment(models.Model):
    """Модель платежа"""

    payer: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="payments", verbose_name="Плательщик"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата платежа")
    stripe_product: models.ForeignKey = models.ForeignKey(
        StripeProduct, null=True, on_delete=models.SET_NULL, related_name="payments", verbose_name="Оплаченный продукт"
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


class Subscription(models.Model):
    """Модель подписки"""

    subscriber: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="Подписчик"
    )
    course: models.ForeignKey = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="accessions", verbose_name="Курс"
    )

    class Meta:
        """Класс настроек отображения"""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["course", "subscriber"]
        unique_together = ["subscriber", "course"]

    def __str__(self) -> str:
        """Строковое отображение объекта подписки"""

        return f"{self.course}: {self.subscriber.email}"
