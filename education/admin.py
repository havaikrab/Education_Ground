from django.contrib import admin

from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Класс представления модели курса в админ-панели Django"""

    list_display = ("id", "name", "preview", "description")
    search_fields = ("name", "description")


@admin.register(Lesson)
class ProductAdmin(admin.ModelAdmin):
    """Класс представления модели урока в админ-панели Django"""

    list_display = ("id", "name", "description", "preview", "link_to_video", "course")
    list_filter = ("course",)
    search_fields = ("name", "description")
