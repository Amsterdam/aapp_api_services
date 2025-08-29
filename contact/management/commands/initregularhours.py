from django.core.management.base import BaseCommand

from contact.models.contact_models import (
    CityOffice,
    CityOfficeOpeningHours,
    RegularOpeningHours,
    WeekDay,
)


class Command(BaseCommand):
    help = "Initialize regular hours for all city offices"

    def handle(self, *args, **options):
        regular_hours = [
            {
                "day_of_week": WeekDay.MONDAY,
                "opens_time": "09:00",
                "closes_time": "17:00",
            },
            {
                "day_of_week": WeekDay.TUESDAY,
                "opens_time": "09:00",
                "closes_time": "17:00",
            },
            {
                "day_of_week": WeekDay.WEDNESDAY,
                "opens_time": "09:00",
                "closes_time": "17:00",
            },
            {
                "day_of_week": WeekDay.THURSDAY,
                "opens_time": "09:00",
                "closes_time": "20:00",
            },
            {
                "day_of_week": WeekDay.FRIDAY,
                "opens_time": "09:00",
                "closes_time": "17:00",
            },
            {
                "day_of_week": WeekDay.SUNDAY,
                "opens_time": None,
                "closes_time": None,
            },
            {
                "day_of_week": WeekDay.SATURDAY,
                "opens_time": None,
                "closes_time": None,
            },
        ]

        city_offices = CityOffice.objects.all()

        for city_office in city_offices:
            opening_hours, _ = CityOfficeOpeningHours.objects.get_or_create(
                city_office=city_office
            )

            for hours in regular_hours:
                RegularOpeningHours.objects.get_or_create(
                    city_office_opening_hours=opening_hours,
                    day_of_week=hours["day_of_week"],
                    defaults={
                        "opens_time": hours["opens_time"],
                        "closes_time": hours["closes_time"],
                    },
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully initialized hours for {city_office.title}"
                )
            )
