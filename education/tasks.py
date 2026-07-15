import logging
import time
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from config.settings import EMAIL_HOST_USER, SENDING_INTERVAL
from users.models import CustomUser

logger = logging.getLogger(__name__)


@shared_task
def send_notices(emails: list, message: str) -> None:
    """Отложенная задача по рассылке пользователям уведомлений"""

    logger.info(f'Рассылка уведомления "{message}" начата.')
    for email in emails:
        try:
            send_mail(
                subject="Education Ground. Обновление материалов.",
                message=message,
                from_email=EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.error(f"Ошибка при обращении к SMTP-серверу: {exc}.")
        time.sleep(SENDING_INTERVAL)
    logger.info(f'Рассылка уведомления "{message}" завершена.')


@shared_task
def deactivate_forgotten_accounts() -> None:
    """Блокирует аккаунты пользователей, которые не заходили в приложение больше 30 дней"""

    month_ago = timezone.now() - timedelta(days=30)
    CustomUser.objects.filter(
        Q(last_login__isnull=False, last_login__lt=month_ago) | Q(last_login__isnull=True, date_joined__lt=month_ago)
    ).update(is_active=False)
