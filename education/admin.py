from django.contrib import admin

from .models import Course, Lesson, Payment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Класс представления модели курса в админ-панели Django"""

    list_display = ("id", "name", "preview", "description")
    search_fields = ("name", "description")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Класс представления модели урока в админ-панели Django"""

    list_display = ("id", "name", "description", "preview", "link_to_video", "course")
    list_filter = ("course",)
    search_fields = ("name", "description")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Класс представления модели платежа в админ-панели Django"""

    list_display = ("id", "payer", "created_at", "paid_course", "paid_lesson", "amount", "method")
    list_filter = ("payer", "paid_course", "paid_lesson", "method")
    search_fields = ("payer", "paid_course", "paid_lesson")
