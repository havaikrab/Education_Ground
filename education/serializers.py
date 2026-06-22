from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import Course, Lesson


class CourseSerializer(ModelSerializer):
    """Сериализатор модели курса"""

    lessons_count = SerializerMethodField()

    class Meta:
        """Параметры сериализатора"""

        model = Course
        fields = "__all__"

    def get_lessons_count(self, course: Course) -> int:
        """Получение количества уроков в текущем курсе"""

        return course.lessons.count()  # type: ignore


class LessonSerializer(ModelSerializer):
    """Сериализатор модели урока"""

    class Meta:
        """Параметры сериализатора"""

        model = Lesson
        fields = "__all__"
