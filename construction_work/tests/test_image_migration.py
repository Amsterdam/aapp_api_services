from uuid import uuid4

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from model_bakery import baker


class ImageMigrationTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        # Isolate the irreversible migration from the current test database schema.
        self.schema = connection.ops.quote_name(f"image_migration_{uuid4().hex}")
        with connection.cursor() as cursor:
            cursor.execute("SHOW search_path")
            self.original_search_path = cursor.fetchone()[0]
            cursor.execute(f"CREATE SCHEMA {self.schema}")
            self.schema_created = True
            cursor.execute(f"SET search_path TO {self.schema}")
        self.addCleanup(self.remove_schema)
        self.old_apps = self.migrate("0022_projectcontact_extra")

    def remove_schema(self):
        if not self.schema_created:
            return
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('search_path', %s, false)",
                [self.original_search_path],
            )
            cursor.execute(f"DROP SCHEMA {self.schema} CASCADE")
        self.schema_created = False

    def _fixture_teardown(self):
        self.remove_schema()

    def migrate(self, name):
        executor = MigrationExecutor(connection)
        target = [("construction_work", name)]
        executor.migrate(target)
        return executor.loader.project_state(target).apps

    def make_legacy_image(self, kind, image_set=123):
        parent = baker.make(self.old_apps.get_model("construction_work", kind))
        image = self.old_apps.get_model(
            "construction_work", f"{kind}Image"
        ).objects.create(
            id=987,
            parent_id=parent.pk,
            image_set=image_set,
            aspectRatio=2.0,
            alternativeText="Legacy description",
        )
        return parent, image

    def test_migrates_all_variants_and_preserves_parent_records(self):
        parents = {}
        for kind in ("Article", "Project"):
            parent, image = self.make_legacy_image(kind)
            parents[kind] = parent
            source = self.old_apps.get_model("construction_work", f"{kind}ImageSource")
            for suffix, width in (("large", 200), ("small", 100)):
                source.objects.create(
                    image=image,
                    uri=f"https://example.com/{suffix}.jpg",
                    width=width,
                    height=width // 2,
                )
            empty_parent = baker.make(
                self.old_apps.get_model("construction_work", kind)
            )
            self.old_apps.get_model("construction_work", f"{kind}Image").objects.create(
                id=988,
                parent_id=empty_parent.pk,
                image_set=124,
                aspectRatio=2.0,
            )

        parents["Article"].projects.add(parents["Project"])

        apps = self.migrate("0023_article_project_drupal_id")
        for kind in parents:
            model = apps.get_model("construction_work", kind)
            self.assertEqual(model.objects.filter(drupal_id__isnull=True).count(), 2)
            model.objects.filter(pk=parents[kind].pk).update(drupal_id=456)

        apps = self.migrate("0024_flatten_image_variants")
        for kind, parent in parents.items():
            model = apps.get_model("construction_work", kind)
            self.assertEqual(model.objects.count(), 2)
            migrated_parent = model.objects.get(pk=parent.pk)
            self.assertEqual(migrated_parent.foreign_id, parent.foreign_id)
            self.assertEqual(migrated_parent.drupal_id, 456)
            if kind == "Article":
                self.assertEqual(
                    list(migrated_parent.projects.values_list("pk", flat=True)),
                    [parents["Project"].pk],
                )
            self.assertEqual(
                model.objects.exclude(pk=parent.pk).get().images.count(), 0
            )
            self.assertEqual(
                list(
                    migrated_parent.images.order_by("width").values_list(
                        "foreign_id", "uri", "width", "height"
                    )
                ),
                [
                    (123, "https://example.com/small.jpg", 100, 50),
                    (123, "https://example.com/large.jpg", 200, 100),
                ],
            )
            image_model = apps.get_model("construction_work", f"{kind}Image")
            with self.assertRaises(IntegrityError), transaction.atomic():
                image_model.objects.create(
                    **{f"{kind.lower()}_id": parent.pk},
                    foreign_id=123,
                    uri="https://example.com/small.jpg",
                    width=10,
                    height=5,
                )
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.exclude(pk=parent.pk).update(drupal_id=456)

        tables = connection.introspection.table_names()
        self.assertNotIn("construction_work_articleimagesource", tables)
        self.assertNotIn("construction_work_projectimagesource", tables)

    def test_copies_multiple_batches_and_requires_image_set_ids(self):
        parent, image = self.make_legacy_image("Project")
        source = self.old_apps.get_model("construction_work", "ProjectImageSource")
        source.objects.bulk_create(
            [
                source(
                    image=image,
                    uri=f"https://example.com/{index}.jpg",
                    width=200,
                    height=100,
                )
                for index in range(1001)
            ]
        )
        apps = self.migrate("0024_flatten_image_variants")
        model = apps.get_model("construction_work", "ProjectImage")
        self.assertEqual(model.objects.filter(project_id=parent.pk).count(), 1001)
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.create(
                project_id=parent.pk,
                uri="https://example.com/missing-id.jpg",
                width=200,
                height=100,
            )

    def test_duplicate_sources_abort_without_removing_legacy_data(self):
        _, image = self.make_legacy_image("Project")
        source = self.old_apps.get_model("construction_work", "ProjectImageSource")
        for _ in range(2):
            source.objects.create(
                image=image, uri="https://example.com/image.jpg", width=200, height=100
            )
        with self.assertRaisesRegex(RuntimeError, "duplicate URI"):
            self.migrate("0024_flatten_image_variants")
        self.assertEqual(source.objects.count(), 2)
        source.objects.order_by("pk").first().delete()
        self.migrate("0024_flatten_image_variants")

    def test_invalid_source_data_aborts_without_removing_legacy_data(self):
        _, image = self.make_legacy_image("Article")
        source = self.old_apps.get_model("construction_work", "ArticleImageSource")
        variant = source.objects.create(
            image=image, uri="x" * 2049, width=200, height=100
        )
        for uri in ("x" * 2049, ""):
            variant.uri = uri
            variant.save()
            with self.assertRaisesRegex(RuntimeError, "between 1 and 2048"):
                self.migrate("0024_flatten_image_variants")
            self.assertEqual(source.objects.count(), 1)
        variant.uri = "https://example.com/image.jpg"
        variant.save()
        image.image_set = 0
        image.save()
        with self.assertRaisesRegex(RuntimeError, "valid image-set ID"):
            self.migrate("0024_flatten_image_variants")
        image.image_set = 123
        image.save()
        self.migrate("0024_flatten_image_variants")
