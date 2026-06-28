from typing import cast

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from education.models import Course, Lesson
from users.models import CustomUser


class IsModerator(BasePermission):
    """Разрешение для всех пользователей, кроме группы Модераторов"""

    message = "Доступ запрещен. Вы не входите в группу модераторов."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Проверяет, является ли пользователь модератором"""

        user = cast(CustomUser, request.user)
        return user.groups.filter(name="Модераторы").exists()


class IsOwner(BasePermission):
    """Разрешение для пользователя - владельца"""

    message = "Доступ ограничен. Вы не являетесь владельцем объекта представления."

    def has_object_permission(self, request: Request, view: APIView, obj: Course | Lesson | CustomUser) -> bool:
        """Проверка, является ли авторизованный пользователь владельцем объекта представления"""

        user = request.user
        if isinstance(obj, CustomUser):
            return bool(obj == user)
        if isinstance(obj, Course):
            return bool(obj.owner == user)
        if isinstance(obj, Lesson):
            return bool(obj.course.owner == user)
        return False
