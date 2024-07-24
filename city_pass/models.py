from datetime import datetime, timedelta, timezone
from uuid import uuid4

from django.conf import settings
from django.db import models


class Session(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    encrypted_adminstration_no = models.CharField(null=True)


class AccessToken(models.Model):
    token = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    session = models.OneToOneField(Session, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super().save(*args, **kwargs)

    def is_valid(self):
        ttl_seconds = settings.TOKEN_TTLS["ACCESS_TOKEN"]
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        now = datetime.now(timezone.utc)
        return now < expiry_time

    def __str__(self) -> str:
        return self.token


class RefreshToken(models.Model):
    token = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super().save(*args, **kwargs)

    def is_valid(self):
        ttl_seconds = settings.TOKEN_TTLS["REFRESH_TOKEN"]
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        return datetime.now(timezone.utc) < expiry_time

    def __str__(self) -> str:
        return self.token
