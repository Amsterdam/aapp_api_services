from django.core.exceptions import ValidationError
from django.test import TestCase

from core.validators import AappDeeplinkValidator


class TestAappDeeplinkValidator(TestCase):
    def setUp(self):
        self.validator = AappDeeplinkValidator()

    def test_valid_deeplinks(self):
        valid_deeplinks = [
            "amsterdam://anything",
            "amsterdam://dash-something",
            "amsterdam://anything/path",
            "amsterdam://trailing/slash/",
            "amsterdam://anything/path/subpath",
            "amsterdam://anything?key=value",
            "amsterdam://anything/path?key=value",
            "amsterdam://trailing/slash/?key=value",
            "amsterdam://anything/path?key=value&key2=value2",
        ]

        for deeplink in valid_deeplinks:
            try:
                self.validator(deeplink)
            except ValidationError as e:
                self.fail(
                    f"AappDeeplinkValidator raised ValidationError unexpectedly for {deeplink}: {e}"
                )

    def test_invalid_deeplinks(self):
        invalid_deeplinks = [
            "amsterdam://",
            "amsterdam://path with spaces",
            "https://notadeeplink.com",
            "",
            "amsterdam:path",
        ]

        for deeplink in invalid_deeplinks:
            with self.assertRaises(
                ValidationError, msg=f"Expected ValidationError for {deeplink}"
            ):
                self.validator(deeplink)

    def test_non_string_input(self):
        invalid_inputs = [123, True, [], {}, None]

        for invalid_input in invalid_inputs:
            with self.assertRaises(ValidationError):
                self.validator(invalid_input)
