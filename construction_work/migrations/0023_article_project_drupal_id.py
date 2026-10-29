from django.core.management.color import no_style
from django.db import migrations, models


def reset_project_contact_sequence(apps, schema_editor):
    project_contact = apps.get_model("construction_work", "ProjectContact")
    sequence_reset_sql = schema_editor.connection.ops.sequence_reset_sql(
        no_style(), [project_contact]
    )
    with schema_editor.connection.cursor() as cursor:
        for sql in sequence_reset_sql:
            cursor.execute(sql)


class Migration(migrations.Migration):
    dependencies = [
        ("construction_work", "0022_projectcontact_extra"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="drupal_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="project",
            name="drupal_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="foreign_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="foreign_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="projectcontact",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.RunPython(reset_project_contact_sequence, migrations.RunPython.noop),
    ]
