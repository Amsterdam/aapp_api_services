import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus


class Command(BaseCommand):
    help = "Import old format module data from CSVs into database"

    def empty_strings_to_none(self, row):
        return {k: v if v else None for k, v in row.items()}

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--replace", type=bool, help="Replace current data with data from CSVs"
        )

    def handle(self, *args, **options):
        replace_arg = options["replace"]

        if replace_arg is True:
            ModuleVersion.objects.all().delete()
            ReleaseModuleStatus.objects.all().delete()
            Module.objects.all().delete()
            AppRelease.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    "Removed all existing data (to make space to new data)!"
                )
            )

        added_modules = []
        with open(f"{settings.CSV_DIR}/module.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                module = Module.objects.filter(slug=row["slug"]).first()
                if module:
                    self.stdout.write(
                        self.style.NOTICE(f"Module already exists: {row['slug']}")
                    )
                    continue

                module = Module(**row)
                module.save()

                added_modules.append(module)

        self.stdout.write(self.style.SUCCESS(f"Added modules: {len(added_modules)}"))

        added_module_versions = []
        with open(f"{settings.CSV_DIR}/moduleversions.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                module = Module.objects.filter(slug=row["moduleSlug"]).first()
                if not module:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Module does not exists: {row['moduleSlug']}"
                        )
                    )
                    return

                module_version = ModuleVersion.objects.filter(
                    module=module, version=row["version"]
                )
                if module_version:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Module version already exists: {row['moduleSlug']}, {row['version']}"
                        )
                    )
                    continue

                row.pop("moduleSlug")
                row["module"] = module

                module_version = ModuleVersion(**row)
                module_version.save()

                added_module_versions.append(module)

        self.stdout.write(
            self.style.SUCCESS(f"Added module versions: {len(added_module_versions)}")
        )

        added_releases = []
        with open(f"{settings.CSV_DIR}/releases.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                release = AppRelease.objects.filter(version=row["version"]).first()
                if release:
                    self.stdout.write(
                        self.style.NOTICE(f"Release already exists: {row['version']}")
                    )
                    return

                row["module_order"] = []

                if release_notes := row.get("releaseNotes"):
                    row["release_notes"] = release_notes

                row.pop("releaseNotes")

                # NOTE: created and modified are not taken from CSV
                # but are overwritten by auto_now(_add) from model definition of AppRelease
                release = AppRelease(**row)
                release.save()

                added_releases.append(release)

        self.stdout.write(self.style.SUCCESS(f"Added releases: {len(added_releases)}"))

        added_module_order = []
        with open(f"{settings.CSV_DIR}/moduleorder.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                release = AppRelease.objects.filter(
                    version=row["releaseVersion"]
                ).first()
                if not release:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Release does not exists: {row['releaseVersion']}"
                        )
                    )
                    return

                # Remove the curly braces and split the string by commas if it's not empty
                module_order_from_row = (
                    row["order"][1:-1].split(",") if row["order"][1:-1] else []
                )

                if (
                    module_order_from_row != []
                    and release.module_order == module_order_from_row
                ):
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Release already has this module order: {row['releaseVersion']}, {row['order']}"
                        )
                    )
                    continue

                for slug in module_order_from_row:
                    m = Module.objects.filter(slug=slug).first()
                    if not m:
                        self.stdout.write(
                            self.style.NOTICE(
                                f"Module in module order does not exist: {slug}"
                            )
                        )
                        return

                release.module_order = module_order_from_row
                release.save()

                added_module_order.append(release)

        self.stdout.write(
            self.style.SUCCESS(f"Added module orders: {len(added_module_order)}")
        )

        added_rms_rows = []
        with open(f"{settings.CSV_DIR}/moduleversionsbyrelease.csv") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter="|", quotechar='"')
            for row in csv_reader:
                row = self.empty_strings_to_none(row)

                release = AppRelease.objects.filter(
                    version=row["releaseVersion"]
                ).first()
                if not release:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Release does not exists: {row['releaseVersion']}"
                        )
                    )
                    return

                module_version = ModuleVersion.objects.filter(
                    module__slug=row["moduleSlug"], version=row["moduleVersion"]
                ).first()
                if not module_version:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Module version does not exist: {row['moduleSlug']}, {row['moduleVersion']}"
                        )
                    )
                    return

                rms = ReleaseModuleStatus.objects.filter(
                    app_release=release, module_version=module_version
                ).first()
                if rms:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Release module version already exsists: {module_version.module.slug} ({module_version.version}) for release {release.version}"
                        )
                    )
                    continue

                rms = ReleaseModuleStatus(
                    app_release=release,
                    module_version=module_version,
                    status=row["status"],
                )
                rms.save()
                added_rms_rows.append(rms)

        self.stdout.write(
            self.style.SUCCESS(
                f"Added release module status rows: {len(added_rms_rows)}"
            )
        )
