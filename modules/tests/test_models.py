from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.forms import ValidationError
from django.test import TestCase

from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus


class TestModuleModel(TestCase):
    def test_slug_must_be_unqiue(self):
        """Test if unique slug is being checked"""
        same_slug = "foobar"
        module_1 = Module(slug=same_slug)
        module_2 = Module(slug=same_slug)

        module_1.save()

        with self.assertRaises(IntegrityError):
            module_2.save()

    def test_default_status_being_active(self):
        """Check if default status of a Module is active"""
        module = Module(slug="foobar")
        module.save()
        self.assertEqual(module.status, Module.Status.ACTIVE)


class TestModuleVersionModel(TestCase):
    def setUp(self):
        self.parent_module = Module(slug="foobar")
        self.parent_module.save()

    def test_cascade_on_module_delete(self):
        """Check if ModuleVersion is deleted, when a related Module is deleted"""
        for i in range(0, 2):
            new_module_version = ModuleVersion(
                module=self.parent_module,
                version=str(i + 1),
                title="foobar_title",
                icon="foobar_icon",
                description="foobar_desc",
            )
            new_module_version.save()

        all_module_versions = ModuleVersion.objects.all()
        self.assertEqual(len(all_module_versions), 2)

        # Deleting parent Module not allowed since it has ModuleVersions
        with self.assertRaises(ProtectedError):
            self.parent_module.delete()

    def test_created_date_set_on_create_and_not_updated(self):
        """Test if created date is set on save but never updated"""

        new_module_version = ModuleVersion(
            module=self.parent_module,
            version="1",
            title="foobar_title",
            icon="foobar_icon",
            description="foobar_desc",
        )
        new_module_version.save()

        created_date_after_save = new_module_version.created
        self.assertIsNotNone(created_date_after_save)

        new_module_version.title = "updated_title"
        new_module_version.save()
        created_date_after_update = new_module_version.created
        self.assertEqual(created_date_after_save, created_date_after_update)

    def test_modified_date_set_on_create_and_updated_on_save(self):
        """Test if created date is set on save but never updated"""

        new_module_version = ModuleVersion(
            module=self.parent_module,
            version="1",
            title="foobar_title",
            icon="foobar_icon",
            description="foobar_desc",
        )
        new_module_version.save()

        modified_date_after_save = new_module_version.modified
        self.assertIsNotNone(modified_date_after_save)

        new_module_version.title = "updated_title"
        new_module_version.save()
        modified_date_after_update = new_module_version.modified
        self.assertNotEqual(modified_date_after_save, modified_date_after_update)

    def test_unique_constraint_between_module_and_version(self):
        module_version_1 = ModuleVersion(
            module=self.parent_module,
            version="1",
            title="foobar_title",
            icon="foobar_icon",
            description="foobar_desc",
        )
        module_version_1.save()

        module_version_1_again = ModuleVersion(
            module=self.parent_module,
            version="1",
            title="foobar_title",
            icon="foobar_icon",
            description="foobar_desc",
        )

        with self.assertRaises(IntegrityError):
            module_version_1_again.save()

    def test_on_delete_for_module_versions(self):
        module_version_1 = ModuleVersion(
            module=self.parent_module,
            version="1",
            title="foobar_title",
            icon="foobar_icon",
            description="foobar_desc",
        )
        module_version_1.save()

        # REVIEW: idem andere reviews

        module_version_1.delete()

        # The module should still exist since it is protected. A module can only be deleted if all module_versions referring to it are deleted.
        parent_module_of_version = Module.objects.filter(
            pk=self.parent_module.pk
        ).first()
        self.assertIsNotNone(parent_module_of_version)


class TestAppReleaseModel(TestCase):
    def test_module_order_slugs_must_be_unique(self):
        """Test if all slugs in module order are unique"""
        module_1 = Module(slug="foo")
        module_1.save()
        module_2 = Module(slug="bar")
        module_2.save()

        app_release = AppRelease(
            version="1.0",
            module_order=["foo", "bar", "foo"],
        )

        with self.assertRaises(ValidationError) as context:
            app_release.save()

        self.assertEqual(
            context.exception.message, "Slugs in module_order are not unique"
        )

    def test_module_order_slugs_must_exist_as_module_slug(self):
        """Test if slugs in module order exists as Modules"""
        app_release = AppRelease(
            version="1.0",
            module_order=["foo", "bar"],
        )

        with self.assertRaises(ValidationError) as context:
            app_release.save()

        self.assertEqual(
            context.exception.message,
            "Given slug 'foo' in module_order does not exist as Module",
        )


class TestReleaseModuleStatusModel(TestCase):
    def setUp(self):
        self.module = Module(slug="foo")
        self.module.save()

        self.app_release = AppRelease(
            version="1.0",
            module_order=["foo"],
        )
        self.app_release.save()

        self.module_version = ModuleVersion(
            module=self.module,
            version="1",
            title="foobar_title",
            icon="foobar_icon",
            description="foobar_desc",
        )
        self.module_version.save()

    def test_default_status_being_active(self):
        """Check if default status of a ReleaseModuleStatus is active"""
        rms = ReleaseModuleStatus(
            app_release=self.app_release,
            module_version=self.module_version,
        )
        rms.save()
        self.assertEqual(rms.status, ReleaseModuleStatus.Status.ACTIVE)

    def test_unique_app_release_module_version_constraint(self):
        rms_1 = ReleaseModuleStatus(
            app_release=self.app_release,
            module_version=self.module_version,
        )
        rms_1.save()

        # Create a new RMS with the same app_release and module_version
        # Which is not allowed
        rms_2 = ReleaseModuleStatus(
            app_release=self.app_release,
            module_version=self.module_version,
        )

        with self.assertRaises(IntegrityError):
            rms_2.save()

    def test_on_delete_on_app_release(self):
        """
        Test the on_delete function in case the referred app_release is deleted.
        """
        rms = ReleaseModuleStatus(
            app_release=self.app_release, module_version=self.module_version
        )
        rms.save()

        # delete the app_release
        self.app_release.delete()

        # Checks if the rms is deleted since the app_release is deleted.
        deleted_rms = ReleaseModuleStatus.objects.filter(pk=rms.pk).first()
        self.assertIsNone(deleted_rms)

    def test_on_delete_on_module_version(self):
        """
        Test the on_delete function in case the referred module_version is deleted
        """
        rms = ReleaseModuleStatus(
            app_release=self.app_release, module_version=self.module_version
        )

        rms.save()

        # delete the module_version
        self.module_version.delete()

        # Is the rms deleted since we deleted the module_version?
        deleted_rms = ReleaseModuleStatus.objects.filter(pk=rms.pk).first()
        self.assertIsNone(deleted_rms)
