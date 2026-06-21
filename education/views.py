from rest_framework import generics
from rest_framework.viewsets import ModelViewSet

from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer


class CourseViewSet(ModelViewSet):
    """Вьюсет для модели курса"""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonCreateAPIView(generics.CreateAPIView):
    """Контроллер создания объекта урока"""

    serializer_class = LessonSerializer


class LessonListAPIView(generics.ListAPIView):
    """Контроллер списка уроков"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Контроллер объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonUpdateAPIView(generics.UpdateAPIView):
    """Контроллер изменения объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonDestroyAPIView(generics.DestroyAPIView):
    """Контроллер удаления объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
