import re

from typing import Optional, Any, Self
from dataclasses import dataclass, field

from .dates import Date
from .places import Place
from . import errors


def clean_cell(cell: Any) -> Optional[str]:
    cell = str(cell).strip()
    return (
        None
        if cell
        in (
            "",
            "never married",
            "no issue",
            "xxx",
            "na",
        )
        else cell
    )


@dataclass
class Marriage:
    spouse: Optional[int] = None
    date: Optional[Date] = None
    place: Optional[Place] = None
    children: list[int] = field(default_factory=list)


@dataclass
class Person:
    id_number: Optional[int] = None
    first: Optional[str] = None
    last: Optional[str] = None
    birth_date: Optional[Date] = None
    birth_place: Optional[Place] = None
    death_date: Optional[Date] = None
    death_place: Optional[Place] = None
    notes: Optional[str] = None

    parents: tuple[Optional[int], Optional[int]] = (None, None)
    marriage: Optional[Marriage] = None

    @staticmethod
    def find_id_numbers(cell: str) -> list[int]:
        return [int(match) for match in re.findall(r"\d+", cell)]

    @staticmethod
    def find_id_number(cell: str) -> Optional[int]:
        matches = Person.find_id_numbers(cell)
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise errors.MultipleReferencesError

    @classmethod
    def from_cells(cls, cells: tuple[list[Any], list[Any]]) -> Self:
        # Ensure cells are all non-empty strings or None.
        data = [[clean_cell(cell) for cell in row] for row in cells]

        person = cls()

        person.id_number = int(data[0][0].strip("# .")) if data[0][0] else None
        person.first = data[1][1].title() if data[1][1] else None
        person.last = data[0][1].title() if data[0][1] else None

        person.notes = "  ".join(cell for cell in (data[0][8:] + data[1][8:]) if cell)

        person.parents = (
            cls.find_id_number(str(data[0][3])) if data[0][3] else None,
            cls.find_id_number(str(data[1][3])) if data[1][3] else None,
        )

        person.birth_date = Date.from_entry(data[0][2]) if data[0][2] else None
        person.death_date = Date.from_entry(data[0][6]) if data[0][6] else None

        try:
            person.birth_place = Place.from_entry(data[1][2])
        except errors.UnknownPlaceNameError:
            errors.show_error(
                "Unknown place name",
                f"#{person.id_number} lists `{data[1][2]}` as place of birth, which was not recognised!",
            )

        try:
            person.death_place = Place.from_entry(data[1][6])
        except errors.UnknownPlaceNameError:
            errors.show_error(
                "Unknown place name",
                f"#{person.id_number} lists `{data[1][6]}` as place of death, which was not recognised!",
            )

        # Try to build up a marriage, which we'll parse later and remove from the Person object

        spouse = cls.find_id_number(str(data[0][4])) if data[0][4] else None
        children = cls.find_id_numbers(
            str(data[0][5]) if data[0][5] else "" + str(data[1][5]) if data[1][5] else ""
        )

        marriage_date = None
        marriage_place = None

        # Marriage date and place are annoyingly stored in the same cell, so we have to separate them
        marriage_date_place = data[1][4]
        if marriage_date_place:
            date_match = Date.search(marriage_date_place)
            if date_match:
                # There was a date in the cell, so we take it and assume the rest is the place
                marriage_date = Date.from_entry(marriage_date_place)
                marriage_place_only = marriage_date_place.replace(date_match[0], "")
                if marriage_place_only:
                    try:
                        marriage_place = Place.from_entry(marriage_place_only)
                    except errors.UnknownPlaceNameError:
                        errors.show_error(
                            "Unknown place name",
                            f"#{person.id_number} lists `{marriage_date_place}` as their place "
                            f"and/or date of marriage. \n`{date_match[0]}` was extracted and "
                            f"parsed as the date `{marriage_date}`, but `{marriage_place_only}` "
                            f"wasn't recognised as a place name!",
                        )
            else:
                # We couldn't find a date, so we assume it's just the place
                try:
                    marriage_place = Place.from_entry(marriage_date_place)
                except errors.UnknownPlaceNameError:
                    errors.show_error(
                        "Unknown place name",
                        f"#{person.id_number} lists `{marriage_date_place}` as their place and/or date of marriage,"
                        f"but neither a date nor a place name could be found!",
                    )

        if spouse or children or marriage_date or marriage_place:
            person.marriage = Marriage(
                spouse=spouse,
                date=marriage_date,
                place=marriage_place,
                children=children,
            )

        return person
