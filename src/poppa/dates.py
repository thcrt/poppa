import re
from dataclasses import dataclass
from typing import Self

from .errors import InvalidDateError

ZEROS_PATTERN = r"0*"
DATE_PATTERNS = (
    # day-month-year/range
    r"(?P<d>[0-3]?[0-9])(?P<sep>[-./])(?P<m>[0-1]?[0-9])(?P=sep)(?:(?P<sy>\d{4})-(?P<ey>\d{4})|(?P<y>\d{4}))",  # noqa: E501
    # year/range-month-day
    r"(?:(?P<sy>\d{4})-(?P<ey>\d{4})|(?P<y>\d{4}))(?P<sep>[-./])(?P<m>[0-1]?[0-9])(?P=sep)(?P<d>[0-3]?[0-9])",  # noqa: E501
    # year/range
    r"(?P<d>)(?P<m>)(?P<sy>\d{4})-(?P<ey>\d{4})|(?P<y>\d{4})",
)


@dataclass
class Date:
    year: int | None = None
    start_year: int | None = None
    end_year: int | None = None
    month: int | None = None
    day: int | None = None
    uncertain: bool = False

    @staticmethod
    def search(entry: str) -> re.Match[str] | None:
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, entry.strip(" .?"))
            if match:
                return match
        return None

    @classmethod
    def from_entry(cls, entry: str) -> Self | None:
        match = cls.search(entry)
        if not match:
            return None

        date = cls(uncertain=("?" in entry))

        # Ensure components aren't just empty strings or entirely zeroes before setting them
        if match["y"] and not re.fullmatch(ZEROS_PATTERN, match["y"]):
            date.year = int(match["y"])
        if match["m"] and not re.fullmatch(ZEROS_PATTERN, match["m"]):
            date.month = int(match["m"])
        if match["d"] and not re.fullmatch(ZEROS_PATTERN, match["d"]):
            date.day = int(match["d"])
        if match["sy"] and not re.fullmatch(ZEROS_PATTERN, match["sy"]):
            date.start_year = int(match["sy"])
        if match["ey"] and not re.fullmatch(ZEROS_PATTERN, match["ey"]):
            date.end_year = int(match["ey"])

        if date.year and (date.start_year or date.end_year):
            raise InvalidDateError

        return date

    def __str__(self) -> str:
        if self.year:
            year = str(self.year)
        elif self.start_year or self.end_year:
            start_year = self.start_year if self.start_year else "????"
            end_year = self.end_year if self.end_year else "????"
            year = f"{start_year}-{end_year}"
        else:
            year = "????"

        month = self.month if self.month else "??"
        day = self.day if self.day else "??"

        return f"{day}/{month}/{year}" + (" (?)" if self.uncertain else "")

    def __rich__(self) -> str:
        return str(self)
