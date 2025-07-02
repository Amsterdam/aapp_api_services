# Created by Jeroen Beekman on 2025-04-08 11:27
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "modules",
            "0006_alter_releasemodulestatus_options_apprelease_modules_and_more",
        ),
    ]

    operations = [
        migrations.RunSQL(
            """
            with sorted_module_versions as ( 
                SELECT
                  stat.id as module_status_id,
                  rel.version as release_version,
                  row_number() OVER (PARTITION BY rel.id order by ordinality) AS sort_order,
                  mm.slug,
                  ver.version as module_version
                FROM modules_releasemodulestatus stat
                join modules_apprelease AS rel
                on rel.id = stat.app_release_id 
                CROSS JOIN LATERAL unnest(rel.module_order) WITH ORDINALITY AS m(module_slug, ordinality)
                join modules_module mm
                on mm.slug = m.module_slug
                join modules_moduleversion ver
                on ver.id = stat.module_version_id 
                and ver.module_id = mm.id
            )
            update modules_releasemodulestatus rms
            set sort_order = sorted.sort_order 
            from sorted_module_versions sorted
            where sorted.module_status_id = rms.id
            ;
            """,
            reverse_sql="""
                with release_module_order as (
                    SELECT 
                      mr.id, 
                      array_agg(mm.slug ORDER BY mrs.sort_order) AS module_order
                    FROM modules_apprelease mr
                    JOIN modules_releasemodulestatus mrs ON mrs.app_release_id = mr.id
                    JOIN modules_moduleversion mmv ON mmv.id = mrs.module_version_id
                    JOIN modules_module mm ON mm.id = mmv.module_id
                    GROUP BY mr.id
                    ORDER BY mr.id
                )
                update modules_apprelease mr 
                set module_order = rmo.module_order 
                from release_module_order rmo 
                where rmo.id = mr.id 
                ;
            """,
        ),
    ]
