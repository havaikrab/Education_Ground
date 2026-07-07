from rest_framework import serializers

from .models import Course, Lesson, Payment, Subscription
from .validators import LinkValidator


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор модели урока"""

    description = serializers.CharField(validators=[LinkValidator(["youtube.com"])])
    link_to_video = serializers.URLField(
        validators=[LinkValidator(["youtube.com"])], required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        """Параметры сериализатора"""

        model = Lesson
        fields = "__all__"

    def to_representation(self, instance: Lesson) -> dict:
        """Сокрытие некоторых данных от пользователей, не являющихся владельцем сериализуемого объекта"""

        data = super().to_representation(instance)
        user = self.context["request"].user
        has_subscription = Subscription.objects.filter(subscriber=user, course=instance.course).exists()
        paid = Payment.objects.filter(payer=user, stripe_product__lesson=instance).exists()
        if (
            instance.course.owner != user
            and not user.groups.filter(name="Модераторы").exists()
            and not has_subscription
            and not paid
        ):
            data.pop("description")
            data.pop("link_to_video")
        return data


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор модели курса"""

    description = serializers.CharField(validators=[LinkValidator(["youtube.com"])])
    relation_status = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    lessons_details = LessonSerializer(read_only=True, many=True, source="lessons")

    class Meta:
        """Параметры сериализатора"""

        model = Course
        fields = [
            "id",
            "name",
            "preview",
            "description",
            "usd_price",
            "owner",
            "relation_status",
            "lessons_count",
            "lessons_details",
        ]
        read_only_fields = ["owner"]

    def get_lessons_count(self, course: Course) -> int:
        """Получение количества уроков в текущем курсе"""

        return course.lessons.count()  # type: ignore

    def get_relation_status(self, course: Course) -> str:
        """Определение статуса отношения курса к пользователю"""

        user = self.context["request"].user
        if course.owner == user:
            return "owner"
        elif Subscription.objects.filter(subscriber=user, course=course).exists():
            return "subscriber"
        return "undefined"

    def to_representation(self, instance: Course) -> dict:
        """Сокрытие некоторых данных от пользователей, не являющихся владельцем сериализуемого объекта"""

        data = super().to_representation(instance)
        user = self.context["request"].user
        if data["relation_status"] == "undefined" and not user.groups.filter(name="Модераторы").exists():
            data.pop("description")
            data.pop("owner")
            data.pop("lessons_details")
        return data


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор модели платежа"""

    class Meta:
        """Параметры сериализатора"""

        model = Payment
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор модели подписки"""

    course_name = serializers.CharField(source="course.name", read_only=True)
    course_preview = serializers.ImageField(source="course.preview", read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    payment_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Параметры сериализатора"""

        model = Subscription
        fields = ["course", "course_name", "course_preview", "payment_status", "payment_amount"]
        read_only_fields = ["course"]

    def get_payment_status(self, subscription: Subscription) -> bool:
        """Метод вычисления статуса оплаты подписки"""

        return bool(subscription.course.course_payments.exists())

    def get_payment_amount(self, subscription: Subscription) -> int:
        """Метод вычисления общей суммы платежей пользователя по подписке"""

        user = self.context["request"].user
        payments = subscription.course.course_payments.filter(payer=user)
        return sum([payment.amount for payment in payments])
