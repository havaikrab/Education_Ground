from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from users.models import CustomUser
from users.permissions import IsModeratorOrOwner, IsNotModerator, IsOwner

from .filters import PaymentFilterSet
from .models import Course, Lesson, Payment
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer


class CourseViewSet(ModelViewSet):
    """Вьюсет для модели курса"""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self) -> QuerySet:
        """Определение списка объектов для отображения"""

        user = self.request.user
        if isinstance(user, CustomUser) and user.groups.filter(name="Модераторы").exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Указание авторизованного пользователя владельцем создаваемого курса"""

        user = self.request.user
        serializer.save(owner=user)

    def get_permissions(self) -> list:
        """Определение разрешений на использование функциональности контроллера"""

        if self.action == "create":
            return [IsAuthenticated(), IsNotModerator()]
        elif self.action == "destroy":
            return [IsAuthenticated(), IsOwner()]
        elif self.action in ["update", "partial_update", "retrieve"]:
            return [IsAuthenticated(), IsModeratorOrOwner()]
        else:
            return [IsAuthenticated()]


class LessonCreateAPIView(generics.CreateAPIView):
    """Контроллер создания объекта урока"""

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsNotModerator]

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Ограничение модераторам создавать собственные уроки и запрет создавать уроки для чужих курсов"""

        user = self.request.user
        if isinstance(user, CustomUser):
            course = serializer.validated_data.get("course")
            if course.owner != user:  # type: ignore
                raise PermissionDenied("Запрещено создавать уроки для чужих курсов")
            serializer.save()


class LessonListAPIView(generics.ListAPIView):
    """Контроллер списка уроков"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self) -> QuerySet:
        """Определение списка объектов для отображения"""

        user = self.request.user
        if isinstance(user, CustomUser) and user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(course__owner=user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Контроллер объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrOwner]


class LessonUpdateAPIView(generics.UpdateAPIView):
    """Контроллер изменения объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrOwner]


class LessonDestroyAPIView(generics.DestroyAPIView):
    """Контроллер удаления объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwner]


class PaymentListAPIView(generics.ListAPIView):
    """Контроллер списка платежей"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilterSet
