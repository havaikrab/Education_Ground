from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from education.models import Course, Lesson
from users.models import CustomUser


class CoursesPermissions(BasePermission):
    """Описание прав на работу с объектами модели Course"""

    message = "Доступ ограничен."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Запрет модераторам создавать или удалять объекты модели Course"""

        user = request.user
        if isinstance(user, CustomUser):
            is_moderator = user.groups.filter(name="Модераторы").exists()
            if hasattr(view, "action") and view.action in ["create", "destroy"]:
                return not is_moderator
            return True
        return False

    def has_object_permission(self, request: Request, view: APIView, obj: Course) -> bool:
        """Проверка, является ли авторизованный пользователь владельцем объекта представления или модератором"""

        user = request.user
        if isinstance(user, CustomUser):
            is_moderator = user.groups.filter(name="Модераторы").exists()
            is_owner = obj.owner == user
            return is_owner or is_moderator
        return False


class IsModeratorOrLessonOwner(BasePermission):
    """Описание прав на работу с объектами модели Lesson"""

    message = "Доступ ограничен."

    def has_object_permission(self, request: Request, view: APIView, obj: Lesson) -> bool:
        """Проверка, является ли авторизованный пользователь владельцем объекта представления или модератором"""

        user = request.user
        if isinstance(user, CustomUser):
            is_moderator = user.groups.filter(name="Модераторы").exists()
            is_owner = obj.course.owner == user
            return is_owner or is_moderator
        return False
