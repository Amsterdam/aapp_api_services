import tempfile
from pathlib import Path
from unittest.mock import patch

from django.urls import reverse

from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase
from bridge.boat_charging.views.terms_view import TermsView


class TestTermsView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-terms")

    def test_public_endpoint_without_access_token_returns_latest_terms(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_terms_dir = Path(tmp_dir)
            (tmp_terms_dir / "1.html").write_text("<p>v1 terms</p>", encoding="utf-8")

            headers = self.api_headers.copy()
            headers.pop("access_token", None)

            with patch.object(TermsView, "terms_dir", tmp_terms_dir):
                response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["content"], "<p>v1 terms</p>")
        self.assertEqual(response.data["version"], 1)

    def test_returns_highest_numeric_version_and_ignores_invalid_filenames(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_terms_dir = Path(tmp_dir)
            (tmp_terms_dir / "1.html").write_text("<p>v1 terms</p>", encoding="utf-8")
            (tmp_terms_dir / "2.html").write_text("<p>v2 terms</p>", encoding="utf-8")
            (tmp_terms_dir / "abc.html").write_text(
                "<p>ignore me</p>", encoding="utf-8"
            )
            (tmp_terms_dir / "3.txt").write_text("ignore me", encoding="utf-8")

            with patch.object(TermsView, "terms_dir", tmp_terms_dir):
                response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version"], 2)
        self.assertEqual(response.data["content"], "<p>v2 terms</p>")

    def test_returns_not_found_when_no_valid_terms_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_terms_dir = Path(tmp_dir)
            (tmp_terms_dir / "invalid.html").write_text(
                "<p>invalid</p>", encoding="utf-8"
            )

            with patch.object(TermsView, "terms_dir", tmp_terms_dir):
                response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)
