# Created by Jeroen Beekman on 2025-04-08 11:27
from django.core.management import call_command
from django.db import migrations, models


def run_loaddata(apps, schema_editor):
    call_command("loaddata", verbosity=0)


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0002_rename_city_office_id_openinghours_city_office_and_more"),
    ]

    operations = [
        migrations.RunSQL("DELETE FROM contact_openinghours;"),
        migrations.RunSQL("DELETE FROM contact_openinghoursexception;"),
        migrations.RemoveField(
            model_name="openinghours",
            name="closes_hours",
        ),
        migrations.RemoveField(
            model_name="openinghours",
            name="closes_minutes",
        ),
        migrations.RemoveField(
            model_name="openinghours",
            name="opens_hours",
        ),
        migrations.RemoveField(
            model_name="openinghours",
            name="opens_minutes",
        ),
        migrations.RemoveField(
            model_name="openinghoursexception",
            name="closes_hours",
        ),
        migrations.RemoveField(
            model_name="openinghoursexception",
            name="closes_minutes",
        ),
        migrations.RemoveField(
            model_name="openinghoursexception",
            name="opens_hours",
        ),
        migrations.RemoveField(
            model_name="openinghoursexception",
            name="opens_minutes",
        ),
        migrations.AddField(
            model_name="openinghours",
            name="closes_time",
            field=models.TimeField(),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="openinghours",
            name="opens_time",
            field=models.TimeField(),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="openinghoursexception",
            name="closes_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="openinghoursexception",
            name="opens_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="openinghours",
            options={
                "verbose_name": "Openingstijd",
                "verbose_name_plural": "Openingstijden",
            },
        ),
        migrations.AlterModelOptions(
            name="openinghoursexception",
            options={
                "verbose_name": "Openingstijden uitzondering",
                "verbose_name_plural": "Openingstijden uitzonderingen",
            },
        ),
        migrations.AlterUniqueTogether(
            name="openinghours",
            unique_together={("city_office", "day_of_week")},
        ),
        migrations.AlterUniqueTogether(
            name="openinghoursexception",
            unique_together={("city_office", "date")},
        ),
        migrations.RunPython(run_loaddata),
    ]
