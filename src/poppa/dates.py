from dataclasses import dataclass
from typing import Optional, Self

from .errors import InvalidDateError

import re

ZEROS_PATTERN = r"0*"
DATE_PATTERNS = (
    r"(?P<d>[0-3]?[0-9])(?P<sep>[-./])(?P<m>[0-1]?[0-9])(?P=sep)(?:(?P<sy>\d{4})-(?P<ey>\d{4})|(?P<y>\d{4}))",  # day-month-year/range
    r"(?:(?P<sy>\d{4})-(?P<ey>\d{4})|(?P<y>\d{4}))(?P<sep>[-./])(?P<m>[0-1]?[0-9])(?P=sep)(?P<d>[0-3]?[0-9])",  # year/range-month-day
    r"(?P<d>)(?P<m>)(?P<sy>\d{4})-(?P<ey>\d{4})|(?P<y>\d{4})",  # year/range
)


@dataclass
class Date:
    year: Optional[int] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    uncertain: bool = False

    @staticmethod
    def search(entry: str) -> Optional[re.Match[str]]:
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, entry.strip(" .?"))
            if match:
                return match
        return None

    @classmethod
    def from_entry(cls, entry: str) -> Optional[Self]:
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
