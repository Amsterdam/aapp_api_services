from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("waste", "0010_manualnotification_affected_routes"),
    ]

    operations = [
        migrations.AddField(
            model_name="manualnotification",
            name="postal_area",
            field=models.CharField(
                blank=True,
                help_text="Selecteer een postcodegebied om de notificatie naar een deelgebied te beperken.",
                max_length=255,
                null=True,
                verbose_name="Postcodegebied",
            ),
        ),
    ]
