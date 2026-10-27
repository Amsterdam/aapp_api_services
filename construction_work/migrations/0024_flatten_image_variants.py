import django.db.models.deletion
from django.db import migrations, models


def copy_image_variants(apps, schema_editor):
    alias = schema_editor.connection.alias
    for kind in ("Article", "Project"):
        source_model = apps.get_model("construction_work", f"{kind}ImageSource")
        destination_model = apps.get_model("construction_work", f"{kind}ImageVariant")
        sources = source_model.objects.using(alias)
        duplicate = (
            sources.values("image_id", "uri")
            .annotate(total=models.Count("pk"))
            .filter(total__gt=1)
            .order_by("image_id", "uri")
            .first()
        )
        if duplicate:
            raise RuntimeError(
                f"Cannot migrate {kind} images: duplicate URI {duplicate['uri']!r} "
                f"for legacy image {duplicate['image_id']}. "
                "Resolve duplicate source rows before retrying."
            )

        variants = []
        for source in sources.select_related("image").order_by("pk").iterator():
            if not source.uri or len(source.uri) > 2048:
                raise RuntimeError(
                    f"Cannot migrate {kind} image source {source.pk}: "
                    "URI must contain between 1 and 2048 characters."
                )
            if source.image.image_set <= 0:
                raise RuntimeError(
                    f"Cannot migrate {kind} image {source.image_id}: "
                    "a valid image-set ID is required."
                )
            variants.append(
                destination_model(
                    **{f"{kind.lower()}_id": source.image.parent_id},
                    foreign_id=source.image.image_set,
                    uri=source.uri,
                    width=source.width,
                    height=source.height,
                )
            )
            if len(variants) == 1000:
                destination_model.objects.using(alias).bulk_create(variants)
                variants = []
        destination_model.objects.using(alias).bulk_create(variants)


class Migration(migrations.Migration):
    dependencies = [
        ("construction_work", "0023_article_project_drupal_id"),
    ]

    operations = [
        migrations.CreateModel(
            name=f"{kind}ImageVariant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("foreign_id", models.BigIntegerField()),
                ("uri", models.URLField(max_length=2048)),
                ("width", models.IntegerField()),
                ("height", models.IntegerField()),
                (
                    kind.lower(),
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to=f"construction_work.{kind.lower()}",
                    ),
                ),
            ],
            options={"unique_together": {(kind.lower(), "uri")}},
        )
        for kind in ("Article", "Project")
    ] + [
        # Legacy metadata is intentionally discarded, so rollback requires a backup.
        migrations.RunPython(copy_image_variants),
        migrations.DeleteModel(name="ArticleImageSource"),
        migrations.DeleteModel(name="ProjectImageSource"),
        migrations.DeleteModel(name="ArticleImage"),
        migrations.DeleteModel(name="ProjectImage"),
        migrations.RenameModel(old_name="ArticleImageVariant", new_name="ArticleImage"),
        migrations.RenameModel(old_name="ProjectImageVariant", new_name="ProjectImage"),
    ]
