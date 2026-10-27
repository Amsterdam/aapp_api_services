from django.db import migrations, models


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
    ]
