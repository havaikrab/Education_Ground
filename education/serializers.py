from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import Course, Lesson, Payment


class LessonSerializer(ModelSerializer):
    """Сериализатор модели урока"""

    class Meta:
        """Параметры сериализатора"""

        model = Lesson
        fields = "__all__"


class CourseSerializer(ModelSerializer):
    """Сериализатор модели курса"""

    lessons_count = SerializerMethodField()
    lessons_details = LessonSerializer(read_only=True, many=True, source="lessons")

    class Meta:
        """Параметры сериализатора"""

        model = Course
        fields = ["id", "name", "preview", "description", "owner", "lessons_count", "lessons_details"]
        read_only_fields = ["owner"]

    def get_lessons_count(self, course: Course) -> int:
        """Получение количества уроков в текущем курсе"""

        return course.lessons.count()  # type: ignore


class PaymentSerializer(ModelSerializer):
    """Сериализатор модели платежа"""

    class Meta:
        """Параметры сериализатора"""

        model = Payment
        fields = "__all__"
