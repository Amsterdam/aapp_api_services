from django.core.exceptions import ValidationError
from django.db import models

DAYS = [
    (0, "Zondag"),
    (1, "Maandag"),
    (2, "Dinsdag"),
    (3, "Woensdag"),
    (4, "Donderdag"),
    (5, "Vrijdag"),
    (6, "Zaterdag"),
]


class CityOffice(models.Model):
    """Model for City Offices"""

    identifier = models.CharField(
        max_length=100, blank=False, unique=True, primary_key=True
    )
    title = models.CharField(max_length=100, blank=False)
    images = models.JSONField(null=True, default=dict)
    street_name = models.CharField(max_length=100, blank=False)
    street_number = models.CharField(max_length=100, blank=False)
    postal_code = models.CharField(max_length=100, blank=False)
    city = models.CharField(max_length=100, blank=False)
    lat = models.FloatField(blank=False)
    lon = models.FloatField(blank=False)
    directions_url = models.CharField(max_length=1000, blank=True)
    appointment = models.JSONField(null=True, blank=True, default=dict)
    visiting_hours_content = models.TextField(null=True, blank=True)
    address_content = models.JSONField(null=True, blank=True, default=dict)
    order = models.IntegerField()

    class Meta:
        unique_together = [["lat", "lon"]]

    def __str__(self):
        return self.title


class OpeningHourAbstract(models.Model):
    """Abstract model for City Offices Opening Hours"""

    class Meta:
        abstract = True

    city_office = models.ForeignKey(
        CityOffice, on_delete=models.CASCADE, verbose_name="Stadskantoor"
    )
    opens_time = models.TimeField()
    closes_time = models.TimeField()

    def clean(self):
        if bool(self.opens_time) != bool(self.closes_time):
            raise ValidationError(
                "Both 'opens_time' and 'closes_time' must be set or both left empty."
            )

        if (self.opens_time and self.closes_time) and (
            self.opens_time >= self.closes_time
        ):
            raise ValidationError("Opens time must be before closes time.")


class OpeningHours(OpeningHourAbstract):
    """Model for City Offices Opening Hours Regular"""

    class Meta:
        verbose_name = "Openingstijd"
        verbose_name_plural = "Openingstijden"
        unique_together = [["city_office", "day_of_week"]]

    day_of_week = models.IntegerField(choices=DAYS, verbose_name="Dag van de week")


class OpeningHoursException(OpeningHourAbstract):
    """Model for City Offices Opening Hours Exceptions"""

    class Meta:
        verbose_name = "Openingstijden uitzondering"
        verbose_name_plural = "Openingstijden uitzonderingen"
        unique_together = [["city_office", "date"]]

    date = models.DateField(verbose_name="Datum")
    opens_time = models.TimeField(null=True, blank=True)
    closes_time = models.TimeField(null=True, blank=True)
