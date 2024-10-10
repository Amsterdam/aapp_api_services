from django.core.management.base import BaseCommand
from django.utils import timezone

from construction_work.models import Project

ONE_YEAR_AGO = one_year_ago = timezone.now() - timezone.timedelta(days=365)


class Command(BaseCommand):
    """Remove old devices"""

    help = "Remove old devices"

    def handle(self, *args, **options):
        hidden_project, created = Project.objects.get_or_create(
            foreign_id=0,
            hidden=True,
            title="Test project voor team communicare",
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created hidden project [{hidden_project.pk=}, {hidden_project.foreign_id=}]"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Hidden project already existed [{hidden_project.pk=}, {hidden_project.foreign_id=}]"
                )
            )
