from unittest import mock

from django.test import TestCase
from django.utils import timezone

from construction_work.management.commands.aligniproxdrupalids import Command
from construction_work.models.project_models import Project


class AlignIproxDrupalIdsTestCase(TestCase):
    @mock.patch.object(
        Command,
        "read_id_mapping_file",
        return_value=[{"iprox_id": 123, "drupal_id": 456}],
    )
    def test_alignment_only_updates_drupal_id(self, _mock_read_mapping):
        project = Project.objects.create(
            foreign_id=123,
            title="Project",
            url="https://example.com",
            publication_date=timezone.now(),
        )
        project.active = False
        project.last_seen = timezone.now() - timezone.timedelta(days=10)
        project.save(update_active=False)
        last_seen = project.last_seen

        Command().handle()

        project.refresh_from_db()
        self.assertEqual(project.drupal_id, 456)
        self.assertFalse(project.active)
        self.assertEqual(project.last_seen, last_seen)
