import re

from rest_framework.serializers import ValidationError


class LinkValidator:
    """Валидатор, запрещающий указывать в строке ссылки на ресурсы кроме разрешенных"""

    def __init__(self, available_domains: list):
        """Передача валидатору списка доступных доменных имен"""

        self.available_domains = available_domains

    def __call__(self, value: str) -> None:
        """Проверка вхождения в проверяемую строку недопустимых ссылок"""

        pattern = re.compile(r"(https?://)?(www\.)?[a-zA-Z0-9\-]+\.[a-z]+")
        matches = pattern.finditer(value)
        for match in matches:
            is_valid = False
            for domain in self.available_domains:
                if domain in match.group():
                    is_valid = True
                    break
            if not is_valid:
                raise ValidationError(f"{match.group()} Ссылка на неподдерживаемый ресурс.")
