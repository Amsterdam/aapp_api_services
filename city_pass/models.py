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

    def is_valid(self) -> bool:
        """Check if the token is passed its globally defined TTL.

        Returns:
            bool: if token is still valid
        """
        now = datetime.now(timezone.utc)
        ttl_seconds = settings.TOKEN_TTLS["ACCESS_TOKEN"]
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        if now >= expiry_time:
            return False
        return True

    def __str__(self) -> str:
        return self.token


class RefreshToken(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    token = models.CharField(max_length=255, unique=True, null=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        """First check for token specific expiration date.
        Then check if the token is passed its globally defined TTL.

        Returns:
            bool: if token is still valid
        """
        now = datetime.now(timezone.utc)
        if self.expires_at and now >= self.expires_at:
            return False

        ttl_seconds = settings.TOKEN_TTLS["REFRESH_TOKEN"]
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        if now >= expiry_time:
            return False
        return True

    def expire(self) -> None:
        """Set forces expiration date, outside of standard TTL"""
        if self.expires_at:
            return
        self.expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.REFRESH_TOKEN_EXPIRATION_TIME
        )
        self.save()

    def __str__(self) -> str:
        return self.token
