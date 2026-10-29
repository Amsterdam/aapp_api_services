from unittest import mock

from django.core.management.base import CommandError
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

    @mock.patch.object(Command, "read_id_mapping_file", return_value=[])
    def test_logs_projects_without_mapping(self, _mock_read_mapping):
        Project.objects.create(
            foreign_id=123,
            title="Unmapped project",
            url="https://example.com",
            publication_date=timezone.now(),
        )

        with self.assertLogs(
            "construction_work.management.commands.aligniproxdrupalids", level="WARNING"
        ) as logs:
            Command().handle()

        self.assertIn("No ID pair found for project with Iprox ID: 123", logs.output[0])

    @mock.patch(
        "construction_work.management.commands.aligniproxdrupalids.load_workbook"
    )
    def test_reads_id_mapping_file(self, load_workbook):
        workbook = mock.MagicMock()
        workbook.active.iter_rows.return_value = iter(
            [("iprox_id", "dvo id"), (123, 456)]
        )
        load_workbook.return_value = workbook

        id_pairs = Command().read_id_mapping_file()

        self.assertEqual(id_pairs, [{"iprox_id": 123, "drupal_id": 456}])
        load_workbook.assert_called_once()
        workbook.close.assert_called_once_with()

    @mock.patch(
        "construction_work.management.commands.aligniproxdrupalids.load_workbook"
    )
    def test_rejects_empty_id_mapping_file(self, load_workbook):
        workbook = mock.MagicMock()
        workbook.active.iter_rows.return_value = iter([])
        load_workbook.return_value = workbook

        with self.assertRaisesMessage(CommandError, "The Excel file is empty"):
            Command().read_id_mapping_file()

        workbook.close.assert_called_once_with()

    @mock.patch(
        "construction_work.management.commands.aligniproxdrupalids.load_workbook"
    )
    def test_rejects_id_mapping_file_without_required_headers(self, load_workbook):
        workbook = mock.MagicMock()
        workbook.active.iter_rows.return_value = iter([("iprox_id", "other")])
        load_workbook.return_value = workbook

        with self.assertRaisesMessage(
            CommandError,
            "The Excel file must contain 'iprox_id' and 'dvo id' columns",
        ):
            Command().read_id_mapping_file()

        workbook.close.assert_called_once_with()
