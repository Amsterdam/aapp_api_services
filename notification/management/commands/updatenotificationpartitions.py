import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)
TABLE_NAME = "notification_notification"
DAYS_TO_KEEP = 30


class Command(BaseCommand):
    help = f"Update partitions of {TABLE_NAME} table"

    def handle(self, *args, **options):
        start_date = datetime.date.today() - datetime.timedelta(days=DAYS_TO_KEEP)

        self.drop_old_notifications(start_date)

    def drop_old_notifications(self, start_date):
        query = f"SELECT drop_chunks('{TABLE_NAME}', older_than => '{start_date}');"
        with connection.cursor() as cursor:
            cursor.execute(query)
        logger.info(f"Deleted old partitions of {TABLE_NAME}")
