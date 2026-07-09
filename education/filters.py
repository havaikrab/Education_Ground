from typing import cast

from django.db.models import QuerySet
from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet, NumberFilter, OrderingFilter
from rest_framework.request import Request

from users.models import CustomUser

from .models import Course, Payment


class PaymentFilterSet(FilterSet):
    """Набор фильтров для модели платежа"""

    paid_course = NumberFilter()
    paid_lesson = NumberFilter()
    ordering = OrderingFilter(fields=("created_at",))
    payment_category = CharFilter(method="filter_by_category")

    class Meta:
        model = Payment
        fields = ["paid_course", "paid_lesson", "method", "payment_category"]

    def filter_by_category(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Сортировка платежей по категориям назначения"""

        if value == "courses":
            return queryset.filter(paid_course__isnull=False)
        elif value == "lessons":
            return queryset.filter(paid_lesson__isnull=False)
        else:
            return queryset


class CourseFilterSet(FilterSet):
    """Набор фильтров для модели курса"""

    preview = BooleanFilter(method="preview_filter", label="Наличие изображения")
    subscription = BooleanFilter(method="subscription_filter", label="Наличие подписки")
    paid = BooleanFilter(method="payment_filter", label="Статус оплаты")

    class Meta:
        model = Course
        fields = {"name": ["icontains"], "owner": ["exact"]}

    def preview_filter(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Фильтр-метод параметра preview"""

        if value is True:
            return queryset.exclude(preview="")
        elif value is False:
            return queryset.filter(preview="")
        return queryset

    def subscription_filter(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Фильтр-метод параметра subscription"""

        request = cast(Request, self.request)
        user = cast(CustomUser, request.user)
        if value is True:
            return queryset.filter(accessions__subscriber=user)
        elif value is False:
            return queryset.exclude(accessions__subscriber=user)
        return queryset

    def payment_filter(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Фильтр-метод параметра paid"""

        request = cast(Request, self.request)
        user = cast(CustomUser, request.user)
        if value is True:
            return queryset.filter(stripe_courses__stripe_payments__payer=user).distinct()
        elif value is False:
            return queryset.exclude(stripe_courses__stripe_payments__payer=user)
        return queryset
