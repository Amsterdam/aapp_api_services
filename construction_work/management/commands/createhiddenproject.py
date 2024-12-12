from django.core.management.base import BaseCommand

from construction_work.models.project_models import Project


class Command(BaseCommand):
    """Create hidden project"""

    help = "Create hidden project "

    def handle(self, *args, **options):
        hidden_project, created = Project.objects.get_or_create(
            foreign_id=0,
            hidden=True,
            title="Test project voor team communicare",
            coordinates_lat=52.370216,
            coordinates_lon=4.895168,
            url="https://app.amsterdam.nl",
            publication_date="2021-01-01T00:00:00Z",
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
