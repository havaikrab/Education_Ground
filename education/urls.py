from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .apps import EducationConfig

app_name = EducationConfig.name

router = DefaultRouter()
router.register("courses", views.CourseViewSet)

urlpatterns: list = [
    path("lessons/", views.LessonListAPIView.as_view(), name="lessons"),
    path("lessons/create/", views.LessonCreateAPIView.as_view(), name="lesson_create"),
    path("lessons/<int:pk>/", views.LessonRetrieveAPIView.as_view(), name="lesson_detail"),
    path("lessons/update/<int:pk>/", views.LessonUpdateAPIView.as_view(), name="lesson_update"),
    path("lessons/delete/<int:pk>/", views.LessonDestroyAPIView.as_view(), name="lesson_delete"),
    path("payments/", views.PaymentListAPIView.as_view(), name="payments"),
    path("courses/<int:pk>/subscribe/", views.OpenStripeSessionAPIView.as_view(), name="subscribe"),
    path("payment_success/", views.StripeSessionRetrieveAPIView.as_view(), name="payment_success"),
    path("courses/<int:pk>/refuse/", views.SubscriptionDeactivateAPIView.as_view(), name="refuse"),
    path("webhook/", views.StripeWebhookAPIView.as_view(), name="webhook"),
]

urlpatterns += router.urls
