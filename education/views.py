from typing import Any, Sequence, cast

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users.models import CustomUser
from users.permissions import IsCourseSubscriber, IsModerator, IsOwner

from .filters import CourseFilterSet, PaymentFilterSet
from .models import Course, Lesson, Payment, Subscription
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer


class CourseViewSet(ModelViewSet):
    """Вьюсет для модели курса"""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filterset_class = CourseFilterSet
    ordering_fields = ["id", "name"]
    search_fields = ["name", "description"]

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Указание авторизованного пользователя владельцем создаваемого курса"""

        user = self.request.user
        serializer.save(owner=user)

    def get_permissions(self) -> Sequence:
        """Определение разрешений на использование функциональности контроллера"""

        if self.action == "create":
            self.permission_classes = [IsAuthenticated & ~IsModerator]
        elif self.action in ["update", "partial_update"]:
            self.permission_classes = [IsAuthenticated & (IsModerator | IsOwner)]
        elif self.action == "retrieve":
            self.permission_classes = [IsAuthenticated & (IsModerator | IsOwner | IsCourseSubscriber)]
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


class SubscriptionActivateAPIView(APIView):
    """Контроллер активации подписки на курс"""

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST-запрос на создание объекта подписки"""

        user = request.user
        course_id = kwargs.get("pk")
        course = get_object_or_404(Course, pk=course_id)
        if course.owner == user:
            return Response(
                {"error": "Запрещено подписываться на собственный курс."}, status=status.HTTP_400_BAD_REQUEST
            )
        subscription, created = Subscription.objects.get_or_create(subscriber=user, course=course)
        if created:
            return Response({"message": "Подписка оформлена"})
        return Response({"message": "Вы уже подписаны на данный курс."}, status=status.HTTP_200_OK)
