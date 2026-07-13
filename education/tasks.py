import logging
import time

from celery import shared_task
from django.core.mail import send_mail

from config.settings import EMAIL_HOST_USER, SENDING_INTERVAL

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
