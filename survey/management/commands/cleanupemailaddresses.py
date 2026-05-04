import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from survey.models import Answer
from survey.named_tuples import QuestionType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete email addresses from survey answers after a retention period."

    def handle(self, *args, **options):
        days_until_email_deletion = settings.DAYS_UNTIL_EMAIL_DELETION
        cutoff = timezone.now() - timezone.timedelta(days=days_until_email_deletion)

        # The update() method returns the number of affected rows (https://docs.djangoproject.com/en/6.0/ref/models/querysets/#update)
        updated_count = (
            Answer.objects.filter(
                survey_version_entry__created_at__lte=cutoff,
                question__question_type=QuestionType.EMAIL.value,
            )
            .exclude(answer="")
            .update(answer="")
        )

        logger.info(
            f"Cleaned {updated_count} email answers older than {days_until_email_deletion} days."
        )
