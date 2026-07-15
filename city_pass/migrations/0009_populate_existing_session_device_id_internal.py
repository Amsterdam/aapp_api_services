import logging

from django.db import migrations
from more_itertools import chunked

logger = logging.getLogger(__name__)
BATCH_SIZE = 1000
NOTIFICATION_DB_ALIAS = "notification"


def update_device_id_internal(apps, schema_editor):
    # Prevent this operation from running when migrations are being executed
    # against another database.
    Session = apps.get_model("city_pass", "Session")
    Device = apps.get_model("notification", "Device")

    session_db = schema_editor.connection.alias
    city_pass_sessions_with_device = (
        Session.objects.using(session_db)
        .filter(device_id__isnull=False, device_id_internal__isnull=True)
        .iterator(chunk_size=BATCH_SIZE)
    )
    for batched_sessions in chunked(city_pass_sessions_with_device, BATCH_SIZE):
        batched_device_ids = {session.device_id for session in batched_sessions}
        device_id_to_internal = dict(
            Device.objects.using(NOTIFICATION_DB_ALIAS)
            .filter(device_id__in=batched_device_ids)
            .values_list("device_id", "pk")
        )

        sessions_to_update = []
        for session in batched_sessions:
            if not device_id_to_internal.get(session.device_id):
                logger.error(
                    "Could not find CityPass session device in Notification Device table"
                )
                continue
            session.device_id_internal = device_id_to_internal[session.device_id]
            sessions_to_update.append(session)

        Session.objects.using(session_db).bulk_update(
            sessions_to_update, ["device_id_internal"]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("city_pass", "0008_session_device_id_internal"),
        ("notification", "0027_device_last_seen"),
    ]

    operations = [
        migrations.RunPython(
            update_device_id_internal,
            reverse_code=migrations.RunPython.noop,
        )
    ]
