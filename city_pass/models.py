from datetime import datetime, timedelta, timezone
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import ForeignKey

from city_pass.exceptions import TokenExpiredException


class Session(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    encrypted_adminstration_no = models.CharField(null=True)
    device_id = models.CharField(max_length=255, unique=True, null=True)


class Budget(models.Model):
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgetten"

    code = models.CharField(max_length=255, unique=True)
    title = models.CharField("Titel", max_length=255)
    description = models.TextField("Omschrijving", null=True, blank=True)
    created_at = models.DateTimeField("Aangemaakt op", auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class PassData(models.Model):
    class Meta:
        unique_together = ["pass_number", "session"]

    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    pass_number = models.CharField(null=False)
    encrypted_transaction_key = models.CharField(null=False)
    budgets = models.ManyToManyField(Budget, verbose_name="Budgetten", blank=True)


class SessionToken(models.Model):
    token = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        """
        This function checks if token is passed its globally defined cut off datetime.

        This datetime represents the moment when new "stadspas" data made available by the organisation.
        This moment happens every year, so the format is "month-day hour:minute" or "%m-%d %H:%M"

        If token is created after cut off datetime, it's valid.
        If token is created before or on cut off datetime, and the current time is after cut off datetime,
        the token is invalid and will be deleted.
        """

        now = datetime.now(timezone.utc)
        cut_off_datetime = settings.TOKEN_CUT_OFF_DATETIME
        current_year = now.year

        cut_off_dt_current_year = datetime.strptime(
            f"{current_year}-{cut_off_datetime} +0000", "%Y-%m-%d %H:%M %z"
        )

        # If token is created after cut off datetime, it's valid
        if self.created_at > cut_off_dt_current_year:
            return True

        # If token was created before or on cut off datetime,
        # and the current time is after cut off datetime,
        # the token is invalid and will be deleted
        if now >= cut_off_dt_current_year:
            self.delete()
            raise TokenExpiredException("Token cut off datetime has passed")

        return True

    def __str__(self) -> str:
        return self.token


class AccessToken(SessionToken):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)

    def is_valid(self) -> bool:
        """Check if the token is passed its globally defined TTL.

        Returns:
            bool: if token is still valid
        """
        super().is_valid()
        now = datetime.now(timezone.utc)

        ttl_seconds = settings.TOKEN_TTLS["ACCESS_TOKEN"]
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        if now >= expiry_time:
            raise TokenExpiredException("Token TTL has passed")

        return True


class RefreshToken(SessionToken):
    expires_at = models.DateTimeField(null=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def is_valid(self) -> bool:
        """First check for token specific expiration date.
        Then check if the token is passed its globally defined TTL.

        Returns:
            bool: if token is still valid
        """
        super().is_valid()
        now = datetime.now(timezone.utc)
        if self.expires_at and now >= self.expires_at:
            raise TokenExpiredException("Token specific expiration date has passed")

        ttl_seconds = settings.TOKEN_TTLS["REFRESH_TOKEN"]
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        if now >= expiry_time:
            raise TokenExpiredException("Token TTL has passed")

        return True

    def expire(self) -> None:
        """Set forces expiration date, outside of standard TTL"""
        if self.expires_at:
            return
        self.expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.REFRESH_TOKEN_EXPIRATION_TIME
        )
        self.save()


class Notification(models.Model):
    class Meta:
        verbose_name = "Notificatie"
        verbose_name_plural = "Notificaties"

    title = models.CharField("Titel", default="Stadspas", max_length=255)
    message = models.TextField("Bericht")
    url = models.URLField(null=True, blank=True)
    budgets = models.ManyToManyField(Budget, verbose_name="Budgetten", blank=True)
    image = models.ImageField(
        "Afbeelding",
        upload_to="city-pass/media/",
        null=True,
        blank=True,
    )
    image_description = models.CharField(
        "Afbeelding omschrijving", max_length=255, null=True, blank=True
    )
    image_set_id = models.CharField(
        "Image Set ID", max_length=255, null=True, blank=True
    )
    created_by = ForeignKey(
        User,
        verbose_name="Aangemaakt door",
        on_delete=models.PROTECT,
        related_name="notifications",
    )
    send_at = models.DateTimeField("Verstuurd op", null=True, blank=True)
    nr_sessions = models.PositiveIntegerField(
        "Aantal berichten verstuurd", default=0, editable=False
    )

    def __str__(self) -> str:
        return f"Notificatie: {self.title[:50]}"
