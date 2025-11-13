from django.core.exceptions import ValidationError
from django.db import models


class WeekDay(models.IntegerChoices):
    SUNDAY = 0, "Zondag"
    MONDAY = 1, "Maandag"
    TUESDAY = 2, "Dinsdag"
    WEDNESDAY = 3, "Woensdag"
    THURSDAY = 4, "Donderdag"
    FRIDAY = 5, "Vrijdag"
    SATURDAY = 6, "Zaterdag"


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


class CityOfficeOpeningHours(models.Model):
    """Model to group opening hours for a city office"""

    class Meta:
        verbose_name = "Openingstijd regulier"
        verbose_name_plural = "Openingstijden regulier"

    city_office = models.ForeignKey(
        CityOffice,
        on_delete=models.CASCADE,
        verbose_name="Stadsloket",
    )

    def __str__(self):
        return f"Openingstijden {self.city_office.title}"


class OpeningHourAbstract(models.Model):
    """Abstract model for City Offices Opening Hours"""

    class Meta:
        abstract = True

    opens_time = models.TimeField(null=True, blank=True)
    closes_time = models.TimeField(null=True, blank=True)

    def clean(self):
        if bool(self.opens_time) != bool(self.closes_time):
            raise ValidationError(
                "Both 'opens_time' and 'closes_time' must be set or both left empty."
            )

        if (self.opens_time and self.closes_time) and (
            self.opens_time >= self.closes_time
        ):
            raise ValidationError("Opens time must be before closes time.")


class RegularOpeningHours(OpeningHourAbstract):
    """Model for regular opening hours per city office"""

    class Meta:
        verbose_name = "Openingstijd"
        verbose_name_plural = "Openingstijden"
        unique_together = [["city_office_opening_hours", "day_of_week"]]

    city_office_opening_hours = models.ForeignKey(
        CityOfficeOpeningHours,
        on_delete=models.CASCADE,
        verbose_name="Openingstijden stadsloket",
    )

    day_of_week = models.IntegerField(
        choices=WeekDay.choices, verbose_name="Dag van de week"
    )

    def __str__(self):
        return WeekDay(self.day_of_week).label


class OpeningHoursException(OpeningHourAbstract):
    """Model for exceptions to regular opening hours"""

    class Meta:
        verbose_name = "Openingstijden uitzondering"
        verbose_name_plural = "Openingstijden uitzonderingen"

    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Reden van de uitzondering",
    )
    date = models.DateField(verbose_name="Datum")
    affected_offices = models.ManyToManyField(
        CityOffice,
        verbose_name="Stadsloketten",
        help_text="Selecteer de stadsloketten waar deze uitzondering voor geldt",
    )
    opens_time = models.TimeField(null=True, blank=True)
    closes_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        if type(self.date) is str:
            return self.__str__()

        date = self.date.strftime("%d-%m-%Y")
        if self.description:
            return f"{self.description} ({date})"
        return date
