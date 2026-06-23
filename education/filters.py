from django.db.models import QuerySet
from django_filters.rest_framework import CharFilter, FilterSet, OrderingFilter

from .models import Payment


class PaymentFilterSet(FilterSet):
    """Набор фильтров для модели платежа"""

    ordering = OrderingFilter(fields=("created_at",))
    payment_category = CharFilter(method="filter_by_category")

    class Meta:
        model = Payment
        fields = ["paid_course", "paid_lesson", "method", "payment_category", "ordering"]

    def filter_by_category(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Сортировка платежей по категориям назначения"""

        if value == "courses":
            return queryset.filter(paid_course__isnull=False)
        elif value == "lessons":
            return queryset.filter(paid_lesson__isnull=False)
        else:
            return queryset
