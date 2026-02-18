from datetime import date

from django.test import TestCase

from waste.services.waste_pdf import WastePDF


class FakeWastePDF(WastePDF):
    def __init__(self):
        super().__init__("fake_address_string")
        self.calls = []

    def add_page(self, *args, **kwargs):
        self.calls.append("add_page")
        return super().add_page(*args, **kwargs)

    def cell(self, *args, **kwargs):
        self.calls.append("add_cell")
        return super().cell(*args, **kwargs)


class WastePDFServiceTest(TestCase):
    def test_pdf_creation(self):
        pdf = FakeWastePDF()
        pdf.add_page()
        days = [date(2026, 1, d) for d in range(1, 20)]
        pdf.draw_pdf_month(2026, 1, days, waste_by_date={})

        assert "add_cell" in pdf.calls

    def test_nr_rows_calculation(self):
        pdf = FakeWastePDF()
        days = [date(2026, 1, d) for d in range(27, 32)]
        n_rows = pdf.count_rows_for_days(year=2026, month=1, days=days)

        self.assertEqual(n_rows, 1)
