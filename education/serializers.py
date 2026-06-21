from rest_framework.serializers import ModelSerializer

from .models import Course, Lesson


class CourseSerializer(ModelSerializer):
    """Сериализатор модели курса"""

    class Meta:
        """Параметры сериализатора"""

        model = Course
        fields = "__all__"


class LessonSerializer(ModelSerializer):
    """Сериализатор модели урока"""

    class Meta:
        """Параметры сериализатора"""

        model = Lesson
        fields = "__all__"
