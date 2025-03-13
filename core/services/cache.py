from django.conf import settings
from django_redis.client import DefaultClient


class CustomRedisClient(DefaultClient):
    def make_key(self, key, version=None):
        key = super().make_key(key, version)
        return f"{settings.SERVICE_NAME}:{key}"
