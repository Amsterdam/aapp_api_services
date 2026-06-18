from unittest.mock import Mock

from django.test import SimpleTestCase

from news.management.commands._stage_runner import (
    ETLStageAborted,
    maybe_garbage_collect,
    run_stage,
)


class RunStageTest(SimpleTestCase):
    def test_run_stage_runs_extract_transform_and_load(self):
        extract = Mock(return_value=[{"id": 1}])
        transform = Mock(return_value=[{"foreign_id": 1}])
        load = Mock(return_value=3)

        created_records = run_stage(
            extract=extract,
            extract_empty_message="No extracted data",
            transform=transform,
            transform_empty_message="No transformed data",
            load=load,
        )

        self.assertEqual(created_records, 3)
        extract.assert_called_once_with()
        transform.assert_called_once_with([{"id": 1}])
        load.assert_called_once_with([{"foreign_id": 1}])

    def test_run_stage_aborts_when_extract_returns_no_data(self):
        transform = Mock()
        load = Mock()

        with self.assertRaisesMessage(
            ETLStageAborted,
            "No extracted data",
        ):
            run_stage(
                extract=Mock(return_value=[]),
                extract_empty_message="No extracted data",
                transform=transform,
                transform_empty_message="No transformed data",
                load=load,
            )

        transform.assert_not_called()
        load.assert_not_called()

    def test_run_stage_aborts_when_transform_returns_no_data(self):
        load = Mock()

        with self.assertRaisesMessage(
            ETLStageAborted,
            "No transformed data",
        ):
            run_stage(
                extract=Mock(return_value=[{"id": 1}]),
                extract_empty_message="No extracted data",
                transform=Mock(return_value=[]),
                transform_empty_message="No transformed data",
                load=load,
            )

        load.assert_not_called()


class MaybeGarbageCollectTest(SimpleTestCase):
    def test_maybe_garbage_collect_runs_when_enabled_and_records_created(self):
        garbage_collect = Mock(return_value=2)
        logger = Mock()

        deleted_count = maybe_garbage_collect(
            created_records=4,
            garbage_collect=garbage_collect,
            enabled=True,
            threshold_seconds=7200,
            logger=logger,
        )

        self.assertEqual(deleted_count, 2)
        garbage_collect.assert_called_once_with(threshold_seconds=7200)
        logger.info.assert_called_once_with(
            "News garbage collector completed.",
            extra={"deleted_count": 2},
        )

    def test_maybe_garbage_collect_skips_without_created_records(self):
        garbage_collect = Mock()
        logger = Mock()

        deleted_count = maybe_garbage_collect(
            created_records=0,
            garbage_collect=garbage_collect,
            enabled=True,
            threshold_seconds=7200,
            logger=logger,
        )

        self.assertEqual(deleted_count, 0)
        garbage_collect.assert_not_called()
        logger.info.assert_called_once_with(
            "News garbage collector skipped because it is disabled."
        )

    def test_maybe_garbage_collect_skips_when_disabled(self):
        garbage_collect = Mock()
        logger = Mock()

        deleted_count = maybe_garbage_collect(
            created_records=4,
            garbage_collect=garbage_collect,
            enabled=False,
            threshold_seconds=7200,
            logger=logger,
        )

        self.assertEqual(deleted_count, 0)
        garbage_collect.assert_not_called()
        logger.info.assert_called_once_with(
            "News garbage collector skipped because it is disabled."
        )
