from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ForeignKey


class WeekDay(models.IntegerChoices):
    SUNDAY = 0, "Zondag"
    MONDAY = 1, "Maandag"
    TUESDAY = 2, "Dinsdag"
    WEDNESDAY = 3, "Woensdag"
    THURSDAY = 4, "Donderdag"
    FRIDAY = 5, "Vrijdag"
    SATURDAY = 6, "Zaterdag"


class NotificationSchedule(models.Model):
    """
    Model to store scheduled notifications.
    """

    device_id = models.CharField(max_length=255, primary_key=True)
    bag_nummeraanduiding_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)


class ManualNotification(models.Model):
    class Meta:
        verbose_name = "Notificatie"
        verbose_name_plural = "Notificaties"

    title = models.CharField("Titel", default="Afvalwijzer", max_length=255)
    message = models.TextField("Bericht")
    created_by = ForeignKey(
        User,
        verbose_name="Aangemaakt door",
        on_delete=models.PROTECT,
        related_name="manual_notifications",
    )
    send_at = models.DateTimeField("Verstuurd op", null=True, blank=True)
    nr_sessions = models.PositiveIntegerField(
        "Aantal berichten verstuurd", default=0, editable=False
    )

    def __str__(self) -> str:
        return f"Notificatie: {self.title[:50]}"


class RecycleLocation(models.Model):
    """
    Model to store recycle locations.
    """

    class Meta:
        verbose_name = "Recyclepunt"
        verbose_name_plural = "Recyclepunten"

    name = models.CharField("Naam", max_length=255)
    city = models.CharField("Plaatsnaam", default="Amsterdam", max_length=100)
    city_district = models.CharField("Stadsdeel", max_length=100, blank=True)
    street = models.CharField("Straatnaam", max_length=1000)
    number = models.IntegerField("Huisnummer", blank=True, null=True)
    addition_letter = models.CharField("Huisletter", blank=True, null=True)
    addition_number = models.CharField("Huisnummertoevoeging", blank=True, null=True)
    postal_code = models.CharField("Postcode", max_length=7)
    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=7)
    longitude = models.DecimalField("Longitude", max_digits=9, decimal_places=7)
    commercial_waste = models.BooleanField("Bedrijfsafval", default=False)

    def __str__(self) -> str:
        return f"Recyclepunt: {self.name[:50]}"


class RecycleLocationOpeningHours(models.Model):
    """Model to group opening hours for a recycle location"""

    class Meta:
        verbose_name = "Openingstijd regulier"
        verbose_name_plural = "Openingstijden regulier"

    recycle_location = models.ForeignKey(
        RecycleLocation,
        on_delete=models.CASCADE,
        verbose_name="Recyclepunt",
    )

    def __str__(self):
        return f"Openingstijden {self.recycle_location.name}"


class OpeningHourAbstract(models.Model):
    """Abstract model for Recycle Location Opening Hours"""

    class Meta:
        abstract = True

    opens_time = models.TimeField(null=True, blank=True, verbose_name="Openingstijd")
    closes_time = models.TimeField(null=True, blank=True, verbose_name="Sluitingstijd")

    def clean(self):
        if bool(self.opens_time) != bool(self.closes_time):
            raise ValidationError(
                "Zowel 'openingstijd' als 'sluitingstijd' moeten beiden ingevuld zijn of allbei leeggelaten worden."
            )

        if (self.opens_time and self.closes_time) and (
            self.opens_time >= self.closes_time
        ):
            raise ValidationError("Openingstijd moet voor sluitingstijd zijn.")


class RegularOpeningHours(OpeningHourAbstract):
    """Model for regular opening hours per recycle location"""

    class Meta:
        verbose_name = "Openingstijd"
        verbose_name_plural = "Openingstijden"
        unique_together = [["recycle_location_opening_hours", "day_of_week"]]

    recycle_location_opening_hours = models.ForeignKey(
        RecycleLocationOpeningHours,
        on_delete=models.CASCADE,
        verbose_name="Openingstijden recyclepunt",
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
    affected_locations = models.ManyToManyField(
        RecycleLocation,
        verbose_name="Recyclepunt",
        help_text="Selecteer de recycle punten waar deze uitzondering voor geldt",
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
