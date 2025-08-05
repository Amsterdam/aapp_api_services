from django.test import TestCase

from core.enums import ChoicesEnum, Module, NotificationType


class ExampleChoicesEnum(ChoicesEnum):
    FOO = "foo"
    BAR = "bar"


class TestChoicesEnum(TestCase):
    def test_choices(self):
        self.assertEqual(ExampleChoicesEnum.choices(), [("foo", "FOO"), ("bar", "BAR")])


class TestNotificationType(TestCase):
    def setUp(self):
        self.module = Module.CONSTRUCTION_WORK
        self.notification_type = NotificationType.CONSTRUCTION_WORK_WARNING_MESSAGE

    def test_get_value(self):
        expected_value = "construction-work:warning-message"
        self.assertEqual(self.notification_type.value, expected_value)

    def test_get_modules_with_types_and_descriptions(self):
        result = NotificationType.get_modules_with_types_and_descriptions()

        # Check if the module exists in the result
        result_modules = [m["module"] for m in result]
        self.assertIn(self.module.value, result_modules)

        # Check the module data structure
        module_data = next(m for m in result if m["module"] == self.module.value)
        self.assertEqual(
            module_data["description"], self.module.notification_description
        )

        # Check that the notification type is in the types list
        expected_type_data = {
            "type": self.notification_type.value,
            "description": self.notification_type._value_.description,
        }
        self.assertIn(expected_type_data, module_data["types"])
