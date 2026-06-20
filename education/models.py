from django.db import models


class Course(models.Model):
    """Модель курса"""

    name: models.CharField = models.CharField(max_length=200, verbose_name="Название курса")
    preview: models.ImageField = models.ImageField(
        upload_to="courses_previews", verbose_name="Превью курса", blank=True, null=True
    )
    description: models.TextField = models.TextField(verbose_name="Описание курса")


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
