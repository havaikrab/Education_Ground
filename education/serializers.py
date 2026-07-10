from rest_framework import serializers

from .models import Course, Lesson, Payment, StripeSession, Subscription
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

        user = self.context["request"].user
        return bool(Payment.objects.filter(stripe_product__course=subscription.course, payer=user).exists())

    def get_payment_amount(self, subscription: Subscription) -> int:
        """Метод вычисления общей суммы платежей пользователя по подписке"""

        user = self.context["request"].user
        payments = Payment.objects.filter(stripe_product__course=subscription.course, payer=user)
        return sum([payment.amount for payment in payments])


class StripeSessionSerializer(serializers.ModelSerializer):
    """Сериализатор модели Stripe-сессии"""

    product = serializers.SerializerMethodField()

    class Meta:
        """Параметры сериализатора"""

        model = StripeSession
        fields = "__all__"

    def get_product(self, session: StripeSession) -> dict:
        """Получение данных о продукте"""

        product_type = None
        product_id = None
        if session.product.course:
            product_type = "course"
            product_id = session.product.course.pk
        if session.product.lesson:
            product_type = "lesson"
            product_id = session.product.lesson.pk
        product_name = session.product.product_name
        product_price = session.product.product_price
        return {
            "product_type": product_type,
            "product_id": product_id,
            "product_name": product_name,
            "product_price": product_price,
        }
