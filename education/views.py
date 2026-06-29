from typing import Sequence, cast

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from users.models import CustomUser
from users.permissions import IsModerator, IsOwner

from .filters import PaymentFilterSet
from .models import Course, Lesson, Payment
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer


class CourseViewSet(ModelViewSet):
    """Вьюсет для модели курса"""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self) -> QuerySet:
        """Определение списка объектов для отображения"""

        queryset = super().get_queryset()
        user = cast(CustomUser, self.request.user)
        if not user.groups.filter(name="Модераторы").exists():
            queryset = queryset.filter(owner=user)
        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Указание авторизованного пользователя владельцем создаваемого курса"""

        user = self.request.user
        serializer.save(owner=user)

    def get_permissions(self) -> Sequence:
        """Определение разрешений на использование функциональности контроллера"""

        if self.action == "create":
            self.permission_classes = [IsAuthenticated & ~IsModerator]
        elif self.action in ["update", "partial_update", "retrieve"]:
            self.permission_classes = [IsAuthenticated & (IsModerator | IsOwner)]
        elif self.action == "destroy":
            self.permission_classes = [IsAuthenticated & IsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class LessonCreateAPIView(generics.CreateAPIView):
    """Контроллер создания объекта урока"""

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & ~IsModerator]

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Запрет создавать уроки для чужих курсов"""

        user = cast(CustomUser, self.request.user)
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

        queryset = super().get_queryset()
        user = cast(CustomUser, self.request.user)
        if not user.groups.filter(name="Модераторы").exists():
            queryset = queryset.filter(course__owner=user)
        return queryset


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Контроллер объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & (IsModerator | IsOwner)]


class LessonUpdateAPIView(generics.UpdateAPIView):
    """Контроллер изменения объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & (IsModerator | IsOwner)]

    def perform_update(self, serializer: BaseSerializer) -> None:
        """Запрет присваивать обновляемый урок чужому курсу"""

        user = cast(CustomUser, self.request.user)
        course = serializer.validated_data.get("course")
        if isinstance(course, Course) and course.owner != user:
            raise PermissionDenied("Запрещено создавать уроки для чужих курсов")
        serializer.save()


class LessonDestroyAPIView(generics.DestroyAPIView):
    """Контроллер удаления объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & IsOwner]


class PaymentListAPIView(generics.ListAPIView):
    """Контроллер списка платежей"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilterSet
