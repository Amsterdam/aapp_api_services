from django.db import migrations, models


def create_missing_device_rows(apps, schema_editor):
    Device = apps.get_model("notification", "Device")
    WasteDevice = apps.get_model("notification", "WasteDevice")
    BurningGuideDevice = apps.get_model("notification", "BurningGuideDevice")

    existing_external_ids = set(Device.objects.values_list("external_id", flat=True))
    referenced_external_ids = set(
        WasteDevice.objects.values_list("device_id", flat=True)
    ) | set(BurningGuideDevice.objects.values_list("device_id", flat=True))

    missing_external_ids = referenced_external_ids - existing_external_ids
    if missing_external_ids:
        Device.objects.bulk_create(
            [
                Device(external_id=external_id, os="unknown")
                for external_id in missing_external_ids
            ],
            ignore_conflicts=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0033_notification_is_visible"),
    ]

    operations = [
        migrations.RunPython(
            create_missing_device_rows,
            migrations.RunPython.noop,
        ),
        migrations.RenameField(
            model_name="wastedevice",
            old_name="device_id",
            new_name="device",
        ),
        migrations.AlterField(
            model_name="wastedevice",
            name="device",
            field=models.OneToOneField(
                db_column="device_id",
                on_delete=models.CASCADE,
                primary_key=True,
                related_name="waste_device",
                serialize=False,
                to="notification.device",
                to_field="external_id",
            ),
        ),
        migrations.RenameField(
            model_name="burningguidedevice",
            old_name="device_id",
            new_name="device",
        ),
        migrations.AlterField(
            model_name="burningguidedevice",
            name="device",
            field=models.OneToOneField(
                db_column="device_id",
                on_delete=models.CASCADE,
                primary_key=True,
                related_name="burning_guide_device",
                serialize=False,
                to="notification.device",
                to_field="external_id",
            ),
        ),
    ]
