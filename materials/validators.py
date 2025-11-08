from rest_framework import serializers
from urllib.parse import urlparse


def validate_youtube_link(value):
    """
    Валидатор для проверки, что ссылка ведет только на youtube.com
    """
    if value:
        parsed_url = urlparse(value)
        # Проверяем, что домен - youtube.com
        if parsed_url.netloc not in ['youtube.com', 'www.youtube.com']:
            raise serializers.ValidationError(
                "Разрешены только ссылки на youtube.com"
            )
    return value


class YouTubeLinkValidator:
    """
    Класс-валидатор для проверки YouTube ссылок
    """
    def __init__(self, field):
        self.field = field

    def __call__(self, attrs):
        value = attrs.get(self.field)
        validate_youtube_link(value)

