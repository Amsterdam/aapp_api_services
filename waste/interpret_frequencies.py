import logging
import re
from datetime import date, datetime, timedelta

MONTHLY_PATTERN = re.compile(r"\d{1}(?:e|de|ste) van de maand")
WEEKLY_PATTERN = re.compile(r"om de \d{1} weken")

logger = logging.getLogger(__name__)


def interpret_frequencies(dates, item, ophaaldagen_list):
    frequency = item.get("frequency") or ""
    if frequency == "":
        pass  # no filtering needed
    elif "oneven" in frequency:
        dates = _filter_even_oneven(dates, even=False)
    elif "even" in frequency:
        dates = _filter_even_oneven(dates, even=True)
    elif "/" in frequency:
        dates = _filter_specific_dates(dates, frequency)
    elif MONTHLY_PATTERN.match(frequency) is not None:
        dates = _filter_nth_weekday_dates(
            dates, weekday=ophaaldagen_list[0], frequency=frequency
        )
    elif WEEKLY_PATTERN.match(frequency) is not None:
        dates = _filter_weekly_frequency(dates, item.get("note"))
    else:
        logger.error(
            f"Unknown frequency pattern '{frequency}' for waste type {item.get('code')}"
        )
        dates = []
    return dates


def _filter_even_oneven(dates: list[date], even: bool) -> list[date]:
    filtered_dates = [d for d in dates if d.isocalendar()[1] % 2 != even]
    return filtered_dates


def _filter_nth_weekday_dates(
    dates: list[date], weekday: int, frequency: str
) -> list[date]:
    def determine_nth_weekday_date(dt: date, weekday: int, n: int) -> bool:
        """
        Return True if date `dt` is the `n`-th occurrence of `weekday` in its month.

        Making use of the difference in days between date and first occurence
        # For example:
        #   n=1 → diff_days in [0, 6]
        #   n=2 → diff_days in [7, 13]
        #   n=3 → diff_days in [14, 20], etc.

        weekday: Monday=0, ..., Sunday=7
        n: occurrence number (1=1st, 2=2nd, 3=3rd, ...)
        """
        # First day of the month
        first = dt.replace(day=1)

        # First occurrence of target weekday in the month
        days_until_target = (weekday - first.weekday()) % 7
        first_occurrence = first + timedelta(days=days_until_target)

        # Compute which occurrence dt is
        diff_days = (dt - first_occurrence).days

        return 7 * (n - 1) <= diff_days <= 7 * n - 1

    # get nth from frequency string
    n = int(frequency[0])
    filtered_dates = [
        d for d in dates if determine_nth_weekday_date(dt=d, weekday=weekday, n=n)
    ]
    return filtered_dates


def _filter_specific_dates(dates: list[date], frequency: str) -> list[date]:
    "Filter dates based on specific dates mentioned in the frequency, e.g. '23-1 / 20-2 / 20-3'"
    specific_dates = _filter_dates_without_year(lookup_string=frequency)

    # get parts with a year
    parts = re.findall(r"\d{1,2}-\d{1,2}-\d{2}", frequency)
    for part in parts:
        date = datetime.strptime(part.strip(), "%d-%m-%y").date()
        specific_dates.append(date)
    return [d for d in dates if d in specific_dates]


def _filter_weekly_frequency(dates: list[date], note: str) -> list[date]:
    "Filter dates based on a weekly frequency mentioned in the note, e.g. 'om de 3 weken'"
    note_dates = _filter_dates_without_year(lookup_string=note)
    return [d for d in dates if d in note_dates]


def _filter_dates_without_year(lookup_string: str) -> list[date]:
    regex_pattern = r"\d{1,2}-\d{1,2}"
    parts = re.findall(regex_pattern, lookup_string)
    specific_dates = []
    today = datetime.today()
    year = today.year
    for part in parts:
        day, month = map(int, part.split("-"))

        # Create a mock date for the current year
        year_date = datetime(year, month, day)

        # If this date has passed already, put it in next year
        if year_date < today:
            year_date = year_date.replace(year=year + 1)

        specific_dates.append(year_date.date())
    return specific_dates
