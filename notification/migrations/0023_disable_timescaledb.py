from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "notification",
            "0022_alter_notificationpushmoduledisabled_unique_together_and_more",
        ),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE TABLE notification_notification_normal (LIKE notification_notification INCLUDING ALL);",
            reverse_sql="DROP TABLE IF EXISTS notification_notification_normal;",
        ),
        migrations.RunSQL(
            "INSERT INTO notification_notification_normal SELECT * FROM notification_notification;",
            reverse_sql="DELETE FROM notification_notification_normal;",
        ),
        migrations.RunSQL(
            "ALTER TABLE notification_notification RENAME TO notification_notification_timescaledb;",
            reverse_sql="ALTER TABLE notification_notification_timescaledb RENAME TO notification_notification;",
        ),
        migrations.RunSQL(
            "ALTER TABLE notification_notification_normal RENAME TO notification_notification;",
            reverse_sql="ALTER TABLE notification_notification RENAME TO notification_notification_normal;",
        ),
        # Add FK
        migrations.RunSQL(
            """
                ALTER TABLE notification_notification
                  ADD CONSTRAINT notification_notification_device_id_fkey
                  FOREIGN KEY (device_id) REFERENCES notification_device(id) ON DELETE CASCADE;
        """,
            reverse_sql="ALTER TABLE notification_notification DROP CONSTRAINT IF EXISTS notification_notification_device_id_fkey;",
        ),
        # Drop FK(s) on the old hypertable
        migrations.RunSQL(
            "ALTER TABLE notification_notification_timescaledb DROP CONSTRAINT notification_notific_device_id_d117c735_fk_notificat;",
            reverse_sql="""
                ALTER TABLE notification_notification_timescaledb
                  ADD CONSTRAINT notification_notific_device_id_d117c735_fk_notificat
                  FOREIGN KEY (device_id) REFERENCES notification_device(id) ON DELETE CASCADE;
        """,
        ),
    ]
