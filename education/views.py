from typing import Any, Sequence, cast

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from stripe import SignatureVerificationError, Webhook

from config.settings import STRIPE_WEBHOOK_SECRET
from users.models import CustomUser
from users.permissions import IsCourseSubscriber, IsLessonBuyer, IsModerator, IsOwner

from .filters import CourseFilterSet, PaymentFilterSet
from .models import Course, Lesson, Payment, StripeProduct, StripeSession, Subscription
from .paginators import EducationPaginator
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer, StripeSessionSerializer
from .services import (
    get_stripe_course_data,
    get_stripe_lesson_data,
    get_stripe_session,
    manage_updating,
    parse_webhook_event,
    update_stripe_session_status,
)


@extend_schema_view(
    create=extend_schema(
        summary="Создание нового курса",
        description="""
Необходима авторизация, пользователи-модераторы не имеют права создавать новые курсы.
В теле запроса нужно указать обязательные ключи "name", "description" и, опционально, ключ "preview"
с соответствующими значениями.
""",
    ),
    list=extend_schema(
        summary="Отображение списка курсов с пагинацией и фильтрацией",
        description="""
Необходима авторизация.
Пользователю, не являющемуся модератором приложения или владельцем курса
отображается только название курса и изображение-аватар.
""",
    ),
    retrieve=extend_schema(
        summary="Отображение деталей курса",
        description="""
Необходима авторизация и права модератора, владельца или подписчика.
Пользователю, имеющему соответствующие права, доступно полное отображение курса,
в противном случае возвращается ошибка со статус-кодом 403.
""",
    ),
    update=extend_schema(
        summary="Полное обновление курса",
        description="""
Необходима авторизация и права модератора или владельца.
В теле запроса необходимо передать обязательные ключи "name" и "description" с соответствующими значениями.
""",
    ),
    partial_update=extend_schema(
        summary="Частичное обновление курса",
        description="""
Необходима авторизация и права модератора или владельца.
В теле запроса нужно указать новые значения для одного или нескольких полей "name", "description" или "preview".
""",
    ),
    destroy=extend_schema(
        summary="Удаление курса со всеми входящими в него уроками",
        description="Необходима авторизация и права владельца.",
    ),
)
class CourseViewSet(ModelViewSet):
    """Вьюсет для модели курса"""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filterset_class = CourseFilterSet
    ordering_fields = ["id", "name"]
    search_fields = ["name", "description"]
    pagination_class = EducationPaginator

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Указание авторизованного пользователя владельцем создаваемого курса"""

        user = self.request.user
        course = serializer.save(owner=user)
        stripe_data = get_stripe_course_data(course)
        StripeProduct.objects.create(course=course, **stripe_data)

    def perform_update(self, serializer: BaseSerializer) -> None:

        course = serializer.save()
        manage_updating(course)

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


@method_decorator(
    name="post",
    decorator=extend_schema(
        summary="Создание урока",
        responses={
            200: OpenApiResponse(description="""
{"id": 1, "name": "Новый урок", "description": "Описание урока", "course": 1, "link_to_video": null, "preview": null}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            400: OpenApiResponse(description="""
- Ошибка валидации данных.
- Не указано одно или несколько обязательных полей "name", "description", "course".
"""),
            403: OpenApiResponse(
                description="""
- Модераторам запрещено создавать уроки.
- Запрещено создавать уроки для чужих курсов.
""",
            ),
        },
    ),
)
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
        lesson = serializer.save()
        stripe_data = get_stripe_lesson_data(lesson)
        StripeProduct.objects.create(lesson=lesson, **stripe_data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        summary="Отображение списка уроков с пагинацией",
        responses={
            200: OpenApiResponse(description="""
{"count": 10, "next": "http://localhost:8000/lessons/?page=2&page_size=2", "previous": null, "results": [
    {"id": 1, "name": "Старый урок", "description": "Описание", "course": 1, "link_to_video": null, "preview": null},
    {"id": 2, "name": "Новый урок", "description": "Описание", "course": 2, "link_to_video": null, "preview": null}]}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
        },
    ),
)
class LessonListAPIView(generics.ListAPIView):
    """Контроллер списка уроков"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = EducationPaginator


@method_decorator(
    name="get",
    decorator=extend_schema(
        summary="Детали урока",
        responses={
            200: OpenApiResponse(description="""
{"id": 1, "name": "Новый урок", "description": "Описание урока", "course": 1, "link_to_video": null, "preview": null}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            403: OpenApiResponse(description="Необходимы права владельца, модератора или подписчика"),
            404: OpenApiResponse(description="Урок не найден."),
        },
    ),
)
class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Контроллер объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & (IsModerator | IsOwner | IsLessonBuyer)]


@method_decorator(
    name="put",
    decorator=extend_schema(
        summary="Изменение урока",
        responses={
            200: OpenApiResponse(description="""
{"id": 1, "name": "Обновленнный", "description": "Новое описание", "course": 1, "link_to_video": null, "preview": null}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            400: OpenApiResponse(description="""
- Ошибка валидации данных.
- Не указано одно или несколько обязательных полей "name", "description", "course".
"""),
            403: OpenApiResponse(
                description="""
- Необходимы права владельца или модератора
- Запрещено присваивать уроки чужим курсам.
""",
            ),
            404: OpenApiResponse(description="Урок не найден."),
        },
    ),
)
@method_decorator(
    name="patch",
    decorator=extend_schema(
        summary="Частичное изменение урока",
        responses={
            200: OpenApiResponse(description="""
{"id": 1, "name": "Обновленнный", "description": "Новое описание", "course": 1, "link_to_video": null, "preview": null}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            400: OpenApiResponse(description="Ошибка валидации данных."),
            403: OpenApiResponse(
                description="""
- Необходимы права владельца или модератора
- Запрещено присваивать уроки чужим курсам.
""",
            ),
            404: OpenApiResponse(description="Урок не найден."),
        },
    ),
)
class LessonUpdateAPIView(generics.UpdateAPIView):
    """Контроллер изменения объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & (IsModerator | IsOwner)]

    def perform_update(self, serializer: BaseSerializer) -> None:
        """Запрет присваивать обновляемый урок чужому курсу"""

        lesson = self.get_object()
        current_course = lesson.course
        new_course = serializer.validated_data.get("course")
        if isinstance(new_course, Course) and current_course.owner != new_course.owner:
            raise PermissionDenied("У изменяемого урока и указанного курса должен быть один и тот же владелец")
        updated_lesson = serializer.save()
        stripe_data = get_stripe_lesson_data(updated_lesson)
        StripeProduct.objects.create(lesson=updated_lesson, **stripe_data)
        if new_course is not None:
            manage_updating(current_course, lesson=lesson, new_course=new_course)
        else:
            manage_updating(current_course, lesson=lesson)


@method_decorator(
    name="delete",
    decorator=extend_schema(
        summary="Удаление урока",
        responses={
            204: OpenApiResponse(description='При удалении возвращается "пустой" объект response.'),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            403: OpenApiResponse(description="Необходимы права владельца."),
            404: OpenApiResponse(description="Урок не найден."),
        },
    ),
)
class LessonDestroyAPIView(generics.DestroyAPIView):
    """Контроллер удаления объекта урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & IsOwner]


@method_decorator(
    name="get",
    decorator=extend_schema(
        summary="Отображение списка платежей с пагинацией и фильтрацией",
        responses={
            200: OpenApiResponse(description="""
{"count": 1, "next": "http://localhost:8000/payments/?page=2&page_size=2", "previous": null, "results": [
    {"id": 1,
    "created_at": "2026-06-12T12:12:12.121212Z",
    "amount": 111,
    "method": "cash",
    "payer": 1,
    "paid_course": 1,
    "paid_lesson": null},
    {"id": 2,
    "created_at": "2026-06-22T22:22:22.222222Z",
    "amount": 333,
    "method": "cashless",
    "payer": 2,
    "paid_course": null,
    "paid_lesson": 2}]}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
        },
    ),
)
class PaymentListAPIView(generics.ListAPIView):
    """Контроллер списка платежей"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilterSet
    pagination_class = EducationPaginator


@method_decorator(
    name="post",
    decorator=extend_schema(
        summary="Оплата подписки",
        description="""
Данный контроллер открывает stripe-сессию для оплаты подписки пользователя на определенный курс.
Предварительно проходит проверка отношений объектов пользователя и выбранного курса.
После удачной проверки в БД создается объект сессии, а клиенту возвращается ссылка на оплату.
Подписка становится доступной пользователю только после подтверждения оплаты сервисом Stripe.
Обработка подтверждений происходит автоматически в webhook-эндпоинте.
""",
        responses={
            200: OpenApiResponse(description='{"session_url": "https://checkout.stripe.com/c/pay/<link_body>}'),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            400: OpenApiResponse(description="""
- Вы уже подписаны на данный курс.
- Запрещено подписываться на собственный курс.
"""),
            404: OpenApiResponse(
                description="Курс не найден.",
            ),
        },
    ),
)
class OpenStripeSessionAPIView(APIView):
    """Контроллер открытия Stripe-сессии для оплаты подписки на курс"""

    def post(self, request: Request, pk: int, *args: Any, **kwargs: Any) -> Response:
        """POST-запрос на ссылку для оплаты"""

        user = cast(CustomUser, request.user)
        course = get_object_or_404(Course, pk=pk)
        if course.owner == user:
            return Response(
                {"error": "Запрещено подписываться на собственный курс."}, status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(subscriber=user, course=course).exists():
            return Response({"error": "Вы уже подписаны на данный курс."}, status=status.HTTP_400_BAD_REQUEST)
        str_product = StripeProduct.objects.get(course=course, is_active=True)
        session = get_stripe_session(str_product, user)
        return Response({"session_url": session.session_url})


@method_decorator(
    name="get",
    decorator=extend_schema(
        summary="Детали сессии",
        description="""
Необходима авторизация. Пользователю доступны только открытые им самим сессии.
Используется для редиректа после оплаты продукта и отслеживания статуса платежа.
""",
        responses={
            200: OpenApiResponse(description="""
{"id": 11, "product": {"product_type": "course", "product_id": 3, "product_name": "course_3", "product_price": 33333},
"session_id": "<stripe_session_id>", "status": "open", "customer": 1,
"session_url": "https://checkout.stripe.com/c/pay/<link-body>"}
"""),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            404: OpenApiResponse(description="Сессия не найдена."),
        },
    ),
)
class StripeSessionRetrieveAPIView(generics.RetrieveAPIView):
    """Эндпоинт успешной оплаты подписки"""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """GET-запрос на получение данных сессии"""

        user = request.user
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response({"error": "Параметр session_id не указан в url."}, status=status.HTTP_400_BAD_REQUEST)
        stripe_session = get_object_or_404(StripeSession, session_id=session_id, customer=user)
        stripe_session = update_stripe_session_status(stripe_session)
        serializer = StripeSessionSerializer(stripe_session)
        return Response(serializer.data)


@method_decorator(
    name="post",
    decorator=extend_schema(
        summary="Обработчик Stripe-вебхуков",
        description="""
Данный контроллер не предназначен для взаимодействия с пользователем.
Обработчик ожидает event-объект от сервиса Stripe, в котором передаются сведения о ранее открытой сессии.
После поступившего post-запроса статус объекта сессии сменяется на "expired" или "complete".
"expired" - означает, что время сессии истекло и платеж не может больше быть осуществлен.
При "complete" в БД сохраняется информация о платеже, а пользователю становится доступен соответствующий продукт.
""",
        responses={
            200: OpenApiResponse(description='Возвращается "пустой" объект response.'),
            400: OpenApiResponse(description="Передача данных с невалидной Stripe-подписью."),
            404: OpenApiResponse(
                description="Курс не найден.",
            ),
        },
    ),
)
@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookAPIView(generics.CreateAPIView):
    """Контроллер автоматической обработки вебхуков"""

    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Получение Event-объекта от Stripe-вебхука"""

        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        try:
            event = Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except SignatureVerificationError:
            return Response({"error": "Невалидная Stripe-подпись."}, status=status.HTTP_400_BAD_REQUEST)

        parse_webhook_event(event)

        return Response(status=status.HTTP_200_OK)


@method_decorator(
    name="delete",
    decorator=extend_schema(
        summary="Удаление подписки",
        responses={
            200: OpenApiResponse(description="Подписка отключена."),
            401: OpenApiResponse(description="Пользователь не авторизован."),
            404: OpenApiResponse(description="Подписка не найдена."),
        },
    ),
)
class SubscriptionDeactivateAPIView(APIView):
    """Контроллер удаления подписки на курс"""

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST-запрос на удаление объекта подписки"""

        user = request.user
        course_id = kwargs.get("pk")
        subscription = get_object_or_404(
            Subscription.objects.select_related("course"), subscriber=user, course_id=course_id
        )
        subscription.delete()
        return Response({"message": "Подписка отключена."}, status=status.HTTP_200_OK)
