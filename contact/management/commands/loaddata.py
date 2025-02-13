import csv
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from contact.models import CityOffice, OpeningHours, OpeningHoursException

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import contact data from CSVs into database"

    def log_info(self, message):
        self.stdout.write(self.style.SUCCESS(message))
        logger.info(message)

    def log_warning(self, message):
        self.stdout.write(self.style.WARNING(message))
        logger.warning(message)

    def log_error(self, message):
        self.stdout.write(self.style.ERROR(message))
        logger.error(message)

    def empty_strings_to_none(self, row):
        return {k: v if v else None for k, v in row.items()}

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--replace", type=bool, help="Replace current data with data from CSVs"
        )

    def handle(self, *args, **options):
        replace_arg = options["replace"]

        if replace_arg is True:
            CityOffice.objects.all().delete()
            self.log_info("Removed all existing data (to make space to new data)!")

        added_city_offices = []
        with open(f"{settings.CSV_DIR}/cityoffices.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                # Transform JSON to dict
                row["images"] = json.loads(row["images"]) if row["images"] else None
                row["appointment"] = (
                    json.loads(row["appointment"]) if row["appointment"] else None
                )
                row["address_content"] = (
                    json.loads(row["address_content"])
                    if row["address_content"]
                    else None
                )

                existing_city_office = CityOffice.objects.filter(
                    identifier=row["identifier"]
                )
                if existing_city_office:
                    self.log_info(
                        f"City office already exists: {row['title']} ({row['identifier']})"
                    )
                    continue

                city_office = CityOffice(**row)
                city_office.save()
                added_city_offices.append(city_office)

        self.log_info(f"Added city office: {len(added_city_offices)}")

        added_opening_hours = []
        with open(f"{settings.CSV_DIR}/openinghoursregular.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                city_office_id = row["city_office_id"]
                city_office = CityOffice.objects.filter(pk=city_office_id).first()
                if not city_office:
                    self.log_error(
                        f"Opening hour can not be added, since city office is not found: {city_office_id}"
                    )
                    continue

                day_of_week = row["day_of_week"]
                existing_opening_hours = OpeningHours.objects.filter(
                    city_office=city_office, day_of_week=day_of_week
                )
                if existing_opening_hours:
                    self.log_info(
                        f"Opening hour for this city office and day already exists: {city_office.title}, day {day_of_week}"
                    )
                    continue

                opening_hours = OpeningHours(**row)
                opening_hours.save()
                added_opening_hours.append(opening_hours)

        self.log_info(f"Added regular opening hours: {len(added_opening_hours)}")

        added_opening_hour_exceptions = []
        with open(f"{settings.CSV_DIR}/openinghoursexceptions.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                city_office_id = row["city_office_id"]
                city_office = CityOffice.objects.filter(pk=city_office_id).first()
                if not city_office:
                    self.log_error(
                        f"Opening hour can not be added, since city office is not found: {city_office_id}"
                    )
                    continue

                date = row["date"]
                existing_opening_hours = OpeningHoursException.objects.filter(
                    city_office=city_office, date=date
                )
                if existing_opening_hours:
                    self.log_info(
                        f"Opening hour exception for this city office and date already exists: {city_office.title}, {date}"
                    )
                    continue

                opening_hours_exception = OpeningHoursException(**row)
                opening_hours_exception.save()
                added_opening_hour_exceptions.append(opening_hours_exception)

        self.log_info(
            f"Added opening hour exceptions: {len(added_opening_hour_exceptions)}"
        )
