from copy import copy

from django.test import TestCase

from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus


class TestCaseWithData(TestCase):
    """Testdata used in unittests"""

    modules = [
        {"slug": "slug0", "status": 1},
        {"slug": "slug1", "status": 1},
        {"slug": "slug2", "status": 1},
        {"slug": "slug3", "status": 1},
        {"slug": "slug4", "status": 1},
        {"slug": "slug5", "status": 1},
    ]

    module_versions = [
        {
            "module": None,
            "title": "title",
            "icon": "icon",
            "version": "1.2.3",
            "description": "description",
        },
        {
            "module": None,
            "title": "title",
            "icon": "icon",
            "version": "1.2.20",
            "description": "description",
        },
        {
            "module": None,
            "title": "title",
            "icon": "icon",
            "version": "1.3.4",
            "description": "description",
        },
        {
            "module": None,
            "title": "title",
            "icon": "icon",
            "version": "1.30.4",
            "description": "description",
        },
        {
            "module": None,
            "title": "title",
            "icon": "icon",
            "version": "2.10.2",
            "description": "description",
        },
        {
            "module": None,
            "title": "title",
            "icon": "icon",
            "version": "10.3.2",
            "description": "description",
        },
    ]

    modules_by_app = [
        {
            "releaseVersion": "0.0.1",
            "moduleSlug": "slug0",
            "moduleVersion": "1.2.3",
            "status": 1,
        },
        {
            "releaseVersion": "0.0.2",
            "moduleSlug": "slug0",
            "moduleVersion": "1.2.3",
            "status": 1,
        },
        {
            "releaseVersion": "0.1.1",
            "moduleSlug": "slug0",
            "moduleVersion": "1.2.20",
            "status": 1,
        },
        {
            "releaseVersion": "0.0.1",
            "moduleSlug": "slug1",
            "moduleVersion": "1.3.4",
            "status": 0,
        },
        {
            "releaseVersion": "0.0.1",
            "moduleSlug": "slug2",
            "moduleVersion": "1.30.4",
            "status": 1,
        },
        {
            "releaseVersion": "0.0.1",
            "moduleSlug": "slug3",
            "moduleVersion": "2.10.2",
            "status": 1,
        },
        {
            "releaseVersion": "0.0.0",
            "moduleSlug": "slug4",
            "moduleVersion": "10.3.2",
            "status": 1,
        },
    ]

    module_order = [
        {"releaseVersion": "0.0.0", "order": ["slug0"]},
        {"releaseVersion": "0.0.1", "order": ["slug0", "slug1", "slug2"]},
    ]

    releases = [
        {
            "version": "0.0.0",
            "release_notes": "release 0.0.0",
            "published": "1970-01-01",
            "unpublished": "1970-12-31",
            "created": "1970-01-01",
            "modified": None,
            "module_order": ["slug4"],
        },
        {
            "version": "0.0.1",
            "release_notes": "release 0.0.1",
            "published": "1971-01-01",
            "unpublished": "1971-12-31",
            "created": "1970-01-01",
            "modified": None,
            "module_order": ["slug0", "slug1", "slug2", "slug3"],
        },
        {
            "version": "0.0.2",
            "release_notes": "release 0.0.2",
            "published": "1971-01-01",
            "unpublished": "1971-12-31",
            "created": "1970-01-01",
            "modified": None,
            "module_order": ["slug0"],
        },
        {
            "version": "0.1.1",
            "release_notes": "release 0.1.1",
            "published": "1971-01-01",
            "unpublished": "1971-12-31",
            "created": "1970-01-01",
            "modified": None,
            "module_order": ["slug0"],
        },
    ]

    def setUp(self):
        modules: list[Module] = []
        module_versions: list[ModuleVersion] = []
        releases: list[AppRelease] = []

        ## Create modules

        for module in self.modules:
            module = Module.objects.create(**module)
            modules.append(module)

        ## Link modules versions to modules

        first_version = self.module_versions[0]
        first_version["module"] = modules[0]
        first_version = ModuleVersion.objects.create(**first_version)
        module_versions.append(first_version)

        second_version = self.module_versions[1]
        second_version["module"] = modules[0]
        second_version = ModuleVersion.objects.create(**second_version)
        module_versions.append(second_version)

        third_version = self.module_versions[2]
        third_version["module"] = modules[1]
        third_version = ModuleVersion.objects.create(**third_version)
        module_versions.append(third_version)

        fourth_version = self.module_versions[3]
        fourth_version["module"] = modules[2]
        fourth_version = ModuleVersion.objects.create(**fourth_version)
        module_versions.append(fourth_version)

        fifth_version = self.module_versions[4]
        fifth_version["module"] = modules[3]
        fifth_version = ModuleVersion.objects.create(**fifth_version)
        module_versions.append(fifth_version)

        sixth_version = self.module_versions[5]
        sixth_version["module"] = modules[4]
        sixth_version = ModuleVersion.objects.create(**sixth_version)
        module_versions.append(sixth_version)

        ## Create releases
        for release in self.releases:
            release = AppRelease.objects.create(**release)
            releases.append(release)

        ## Link module versions to releases
        release_module_status_template = {
            "app_release": None,
            "module_version": None,
            "status": 1,
        }

        # app release 0.0.1
        first_release = copy(release_module_status_template)
        first_release["app_release"] = releases[1]
        first_release["module_version"] = module_versions[0]
        ReleaseModuleStatus.objects.create(**first_release)

        # app release 0.0.1
        second_release = copy(release_module_status_template)
        second_release["app_release"] = releases[1]
        second_release["module_version"] = module_versions[2]
        ReleaseModuleStatus.objects.create(**second_release)

        # app release 0.0.1
        third_release = copy(release_module_status_template)
        third_release["app_release"] = releases[1]
        third_release["module_version"] = module_versions[3]
        ReleaseModuleStatus.objects.create(**third_release)

        # app release 0.0.1
        fourth_release = copy(release_module_status_template)
        fourth_release["app_release"] = releases[1]
        fourth_release["module_version"] = module_versions[4]
        ReleaseModuleStatus.objects.create(**fourth_release)

        # app release 0.0.2
        fifth_release = copy(release_module_status_template)
        fifth_release["app_release"] = releases[2]
        fifth_release["module_version"] = module_versions[0]
        ReleaseModuleStatus.objects.create(**fifth_release)

        # app release 0.1.1
        sixth_release = copy(release_module_status_template)
        sixth_release["app_release"] = releases[3]
        sixth_release["module_version"] = module_versions[1]
        ReleaseModuleStatus.objects.create(**sixth_release)

        # app release 0.0.0
        seventh_release = copy(release_module_status_template)
        seventh_release["app_release"] = releases[0]
        seventh_release["module_version"] = module_versions[5]
        ReleaseModuleStatus.objects.create(**seventh_release)
