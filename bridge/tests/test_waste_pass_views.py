from rest_framework import status

from bridge.constants import waste_pass_constants
from bridge.enums import District
from core.tests.test_authentication import BasicAPITestCase


class TestWastePassNumberView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = "/waste/api/v1/pass-number"

    # Override constants
    waste_pass_constants.DISTRICT_POSTAL_CODE_MAPPING = {
        District.NOORD: [("1000", "1003")],
        District.OOST: [("1004", "1007")],
        District.ZUID: [("1008", "1009")],
    }
    waste_pass_constants.POSTAL_CODE_CONTAINER_NOT_PRESENT = {
        ("1000", "1000"): ["AB"],
        ("1001", "1001"): ["AB"],
        ("1002", "1003"): [],
    }
    waste_pass_constants.DISTRICT_PASS_NUMBER_MAPPING = {
        District.NOORD: "0123456789",
        District.ZUID: "0123456789",
    }

    def test_valid_postal_code_with_pass(self):
        valid_cases = [
            ("1000AA", District.NOORD),
            ("1001 aa", District.NOORD),
            ("1008aa", District.ZUID),
        ]

        for postal_code, district in valid_cases:
            response = self.client.get(
                f"{self.url}?postal_code={postal_code}", headers=self.api_headers
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["district"], district.value)
            self.assertEqual(response.data["pass_number"], "0123456789")
            self.assertEqual(response.data["has_container"], True)

    def test_district_not_found(self):
        """Test when postal code doesn't match any district"""
        response = self.client.get(
            f"{self.url}?postal_code=9999ZZ", headers=self.api_headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pass_number_not_found(self):
        """Test when district exists but has no pass number mapping"""
        # This assumes there's a district in settings without a pass number mapping
        response = self.client.get(
            f"{self.url}?postal_code=1004AA", headers=self.api_headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valid_postal_code_without_container(self):
        invalid_cases = [
            "1000AB",
            "1001 AB",
            "1002 ab",
            "1003 ab",
        ]

        for postal_code in invalid_cases:
            response = self.client.get(
                f"{self.url}?postal_code={postal_code}", headers=self.api_headers
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["has_container"], False)

    def test_invalid_postal_codes(self):
        invalid_cases = [
            "12345A",
            "123ABC",
            "1234A1",
            "123",
            "ABCDEF",
        ]

        for postal_code in invalid_cases:
            response = self.client.get(
                f"{self.url}?postal_code={postal_code}", headers=self.api_headers
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_postal_code(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("postal_code", response.data)

    def test_valid_house_numbers(self):
        valid_cases = [
            "postal_code=1000AA&house_number=42",
            "postal_code=1000AA&house_number=1",
            "postal_code=1000AA",  # House number is optional
        ]

        for url_suffix in valid_cases:
            response = self.client.get(
                f"{self.url}?{url_suffix}", headers=self.api_headers
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_house_numbers(self):
        invalid_cases = [
            "42A",
            "ABC",
            "12.3",
        ]

        for house_number in invalid_cases:
            response = self.client.get(
                f"{self.url}?postal_code=1086AB&house_number={house_number}",
                headers=self.api_headers,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
