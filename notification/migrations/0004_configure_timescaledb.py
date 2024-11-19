from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0003_alter_notification_client_id"),
    ]

    operations = [
        # Remove the primary key constraint in order to create the hypertable
        migrations.RunSQL(
            "ALTER TABLE notification_notification DROP CONSTRAINT notification_notification_pkey;"
        ),
        # 1 day chunk_time_interval is necessary for the retention policy to drop old notifications every day
        # number_partitions refers to the partitioning_column, which is client_id in this case
        migrations.RunSQL(
            """
            SELECT create_hypertable(
                'notification_notification',
                'created_at',
                chunk_time_interval => INTERVAL '1 day',
                partitioning_column => 'client_id',
                number_partitions => 32
            );
            """
        ),
        # Add te primary key constraint again
        migrations.RunSQL(
            "ALTER TABLE public.notification_notification ADD CONSTRAINT notification_notification_pkey PRIMARY KEY (id, created_at, client_id)"
        ),
    ]
