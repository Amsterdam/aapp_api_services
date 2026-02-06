import calendar
import os
from datetime import date
from io import BytesIO
from urllib.parse import quote

import qrcode
from babel.dates import format_date
from fpdf import FPDF

# pdf settings
LABEL_TO_IMAGE = {
    "Papier en karton": "paper.svg",
    "Grof afval": "grof.svg",
    "Restafval": "rest.svg",
    "Groente-, fruit-, etensresten en tuinafval": "gft.svg",
}
PDF_ICON_SIZE = 6
PDF_ROW_HEIGHT = 20
PDF_MARGIN_LR = 30
PDF_MARGIN_TB = 10
PDF_FONT = "Helvetica"
PDF_TITLE_FONT_SIZE = 21
PDF_MONTH_HEADER_FONT_SIZE = 13
PDF_REGULAR_FONT_SIZE = 10
PDF_HEADER_FONT_SIZE = 8
PDF_TITLE_CELL_HEIGHT = int(PDF_TITLE_FONT_SIZE / 1.6)
PDF_MONTH_HEADER_CELL_HEIGHT = int(PDF_MONTH_HEADER_FONT_SIZE / 1.6)
PDF_REGULAR_CELL_HEIGHT = int(PDF_REGULAR_FONT_SIZE / 1.6)
PDF_HEADER_CELL_HEIGHT = int(PDF_HEADER_FONT_SIZE / 1.6)
QR_HEIGHT = 20
LEGEND_LINES = len(LABEL_TO_IMAGE)
LEGEND_LINE_HEIGHT = PDF_REGULAR_CELL_HEIGHT + 3
WEEKDAYS_NL = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class WastePDF(FPDF):
    def __init__(self, address):
        super().__init__()
        self.set_margins(PDF_MARGIN_LR, PDF_MARGIN_TB, PDF_MARGIN_LR)
        self.address = address
        self._set_pdf_settings()

    def header(self):
        start_date = date.today()
        self.set_text_color(0, 0, 0)
        self.set_font(PDF_FONT, "", PDF_HEADER_FONT_SIZE)
        self.cell(0, PDF_HEADER_CELL_HEIGHT, "Gemeente Amsterdam", align="L")
        self.cell(
            0,
            PDF_HEADER_CELL_HEIGHT,
            f"{format_date(start_date, 'd MMMM YYYY', locale='nl')}",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_font(PDF_FONT, "B", PDF_HEADER_FONT_SIZE)
        self.cell(
            0, PDF_HEADER_CELL_HEIGHT, f"{self.address}", new_x="LMARGIN", new_y="NEXT"
        )

    def footer(self):
        self.set_text_color(0, 0, 0)
        self.set_font(PDF_FONT, "B", PDF_REGULAR_FONT_SIZE)

        required_height = max(
            QR_HEIGHT + 2 * PDF_REGULAR_CELL_HEIGHT, (LEGEND_LINES * LEGEND_LINE_HEIGHT)
        )
        self.set_y(-(required_height + 10))

        qr_code_y = self.get_y()

        # draw qr code
        qr = qrcode.QRCode(border=0)
        qr.add_data(
            f"https://www.amsterdam.nl/afval/afvalinformatie/?adres={quote(self.address)}"
        )
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save QR code to memory
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Insert QR code into PDF
        self.image(
            buffer, x=self.w - self.r_margin - QR_HEIGHT, y=qr_code_y, w=QR_HEIGHT
        )
        self.set_y(-10 - (2 * PDF_HEADER_CELL_HEIGHT))

        self.set_text_color(0, 0, 0)
        self.set_font(PDF_FONT, "", PDF_HEADER_FONT_SIZE)
        self.cell(
            0,
            PDF_HEADER_CELL_HEIGHT - 2,
            "Bekijk alle ophaaldagen op:",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.cell(
            0,
            PDF_HEADER_CELL_HEIGHT - 2,
            "https://www.amsterdam.nl/afval/afvalinformatie",
            align="R",
            new_x="LMARGIN",
        )

        self.set_font(PDF_FONT, "B", PDF_REGULAR_FONT_SIZE)
        self.set_y(-(required_height + 10))

        # draw legend
        for waste_name, waste_icon in LABEL_TO_IMAGE.items():
            self.image(
                f"{DIR_PATH}/pdf_icons/{waste_icon}",
                x=self.get_x(),
                y=self.get_y(),
                w=PDF_ICON_SIZE,
                h=PDF_ICON_SIZE,
            )
            self.set_x(self.get_x() + PDF_ICON_SIZE + 1)
            self.cell(
                0,
                PDF_REGULAR_CELL_HEIGHT,
                waste_name,
                new_x="LMARGIN",
                new_y="NEXT",
            )
            self.ln(3)

        # Printing page number:
        self.set_font(PDF_FONT, "", PDF_HEADER_FONT_SIZE)
        self.cell(
            0,
            PDF_HEADER_CELL_HEIGHT - 2,
            f"Pagina {self.page_no()} van {{nb}}",
            align="R",
        )

    def add_title(self):
        start_date = date.today()
        self.set_font(PDF_FONT, "B", PDF_TITLE_FONT_SIZE)
        self.cell(
            0,
            PDF_TITLE_CELL_HEIGHT,
            f"Afvalkalender {start_date.year}",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    def remaining_page_height(self):
        return (
            self.h
            - self.b_margin
            - max(QR_HEIGHT, (LEGEND_LINES * LEGEND_LINE_HEIGHT))
            - self.get_y()
        )

    def _set_pdf_settings(self) -> tuple:
        self.right_margin = self.w - self.r_margin
        content_width = self.right_margin - self.l_margin
        self.col_width = content_width / 7

    def draw_pdf_month(
        self,
        year: int,
        month: int,
        days: list[date],
        waste_by_date: dict[date, list[str]],
    ):
        # Month title
        self.ln(16)
        self.set_font(PDF_FONT, "B", PDF_MONTH_HEADER_FONT_SIZE)
        self.set_text_color(0, 0, 0)
        month_name = format_date(date(year, month, 1), "MMMM", locale="nl")
        self.cell(
            0,
            PDF_MONTH_HEADER_CELL_HEIGHT,
            month_name.capitalize(),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Weekday header
        self.draw_weekday_header()

        first_weekday = date(year, month, 1).weekday()  # Monday=0
        last_day = calendar.monthrange(year, month)[1]

        day_map = {d.day: d for d in days}

        row_y = self.get_y() + 2
        col = first_weekday
        n_icons_list = []

        for day_num in range(1, last_day + 1):
            if day_num not in day_map:
                col += 1
                if col == 7:
                    self.ln(PDF_ROW_HEIGHT - 2)
                    col = 0
                continue

            current = day_map[day_num]
            x = self.l_margin + col * self.col_width
            self.set_xy(x, row_y)

            is_weekend = current.weekday() >= 5
            # Weekend styling
            if is_weekend:
                self.set_text_color(160, 160, 160)
            else:
                self.set_text_color(0, 0, 0)

            # Day number
            self.set_font(PDF_FONT, "", PDF_REGULAR_FONT_SIZE)
            self.cell(
                self.col_width,
                PDF_REGULAR_CELL_HEIGHT,
                str(day_num),
                align="C",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            n_icons_list.append(len(waste_by_date.get(current, [])))

            # Icons
            for i, waste_name in enumerate(waste_by_date.get(current, [])):
                self.image(
                    f"{DIR_PATH}/pdf_icons/{LABEL_TO_IMAGE[waste_name]}",
                    x + (self.col_width - PDF_ICON_SIZE) / 2,
                    self.get_y() + (PDF_ICON_SIZE + 1) * i,
                    w=PDF_ICON_SIZE,
                    h=PDF_ICON_SIZE,
                )

            col += 1
            if col == 7:
                max_icons = max(n_icons_list)
                # pdf.ln((max_icons * PDF_ICON_SIZE) + PDF_REGULAR_CELL_HEIGHT - 2)
                self.ln(
                    max(
                        (max_icons * PDF_ICON_SIZE) + PDF_REGULAR_CELL_HEIGHT - 2,
                        PDF_ROW_HEIGHT - 2,
                    )
                )
                y_start = self.get_y()
                self.set_line_width(0.2)
                self.set_draw_color(160, 160, 160)
                # Week separator
                self.line(
                    self.l_margin,
                    y_start,
                    self.right_margin,
                    y_start,
                )
                row_y = self.get_y()
                col = 0
                n_icons_list = []

        self.ln(6)

    def draw_weekday_header(self):
        self.set_font(PDF_FONT, "B", PDF_HEADER_FONT_SIZE)
        self.set_text_color(0, 0, 0)
        for i, name in enumerate(WEEKDAYS_NL):
            self.set_xy(self.l_margin + i * self.col_width, self.get_y())
            self.cell(self.col_width, PDF_HEADER_CELL_HEIGHT, name, align="C")

        # Horizontal black line below weekday header
        self.ln(PDF_HEADER_CELL_HEIGHT)
        y_start = self.get_y()
        self.set_line_width(0.5)
        self.set_draw_color(0, 0, 0)
        self.line(
            self.l_margin,
            y_start,
            self.right_margin,
            y_start,
        )

    def estimate_month_height(self, year, month, month_days):
        # Static parts
        title_height = 16 + PDF_MONTH_HEADER_CELL_HEIGHT
        weekday_header_height = PDF_HEADER_CELL_HEIGHT
        bottom_spacing = 6

        # Rows
        n_rows = self.count_rows_for_days(year, month, month_days)
        rows_height = n_rows * PDF_ROW_HEIGHT

        return title_height + weekday_header_height + rows_height + bottom_spacing

    @staticmethod
    def count_rows_for_days(year, month, days):
        first_weekday = date(year, month, 1).weekday()  # Monday = 0

        rows = set()

        for d in days:
            # Day index within the calendar grid
            day_index = first_weekday + (d.day - 1)

            # Which row (week) this day is in
            row = day_index // 7

            rows.add(row)

        return len(rows)
