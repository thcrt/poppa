import re
from dataclasses import dataclass, field
from itertools import batched
from typing import Any, Self

from . import errors
from .dates import Date
from .places import PlacesManager


def clean_cell(cell: Any) -> str | None:
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
    spouse: int | None = None
    date: Date | None = None
    place: PlacesManager.Place | None = None
    children: list[int] = field(default_factory=list)


@dataclass
class Person:
    id_number: int | None = None
    first: str | None = None
    last: str | None = None
    birth_date: Date | None = None
    birth_place: PlacesManager.Place | None = None
    death_date: Date | None = None
    death_place: PlacesManager.Place | None = None
    notes: str | None = None

    parents: tuple[int | None, int | None] = (None, None)
    marriage: Marriage | None = None

    @staticmethod
    def find_id_numbers(cell: str) -> list[int]:
        return [int(match) for match in re.findall(r"\d+", cell)]

    @staticmethod
    def find_id_number(cell: str) -> int | None:
        matches = Person.find_id_numbers(cell)
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise errors.MultipleReferencesError

    @classmethod
    def from_cells(cls, cells: tuple[list[Any], list[Any]], places_manager: PlacesManager) -> Self:
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
            person.birth_place = places_manager.from_entry(data[1][2])
        except errors.UnknownPlaceNameError:
            errors.show_error(
                "Unknown place name",
                f"#{person.id_number} lists `{data[1][2]}` as place of birth, which couldn't be "
                f"recognised as a place!",
            )

        try:
            person.death_place = places_manager.from_entry(data[1][6])
        except errors.UnknownPlaceNameError:
            errors.show_error(
                "Unknown place name",
                f"#{person.id_number} lists `{data[1][6]}` as place of death, which couldn't be "
                f"recognised as a place!!",
            )

        spouse = cls.find_id_number(str(data[0][4])) if data[0][4] else None
        children = cls.find_id_numbers(
            str(data[0][5]) if data[0][5] else "" + str(data[1][5]) if data[1][5] else ""
        )

        marriage_date = None
        marriage_place = None

        # Marriage date and place are stored in the same cell, so we have to separate them
        marriage_date_place = data[1][4]
        if marriage_date_place:
            date_match = Date.search(marriage_date_place)
            if date_match:
                # There was a date in the cell, so we take it and assume the rest is the place
                marriage_date = Date.from_entry(marriage_date_place)
                marriage_place_only = marriage_date_place.replace(date_match[0], "")
                if marriage_place_only:
                    try:
                        marriage_place = places_manager.from_entry(marriage_place_only)
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
                    marriage_place = places_manager.from_entry(marriage_date_place)
                except errors.UnknownPlaceNameError:
                    errors.show_error(
                        "Unknown place name",
                        f"#{person.id_number} lists `{marriage_date_place}` as their place and/or "
                        f"date of marriage, but neither a date nor a place name could be found!",
                    )

        if spouse or children or marriage_date or marriage_place:
            person.marriage = Marriage(
                spouse=spouse,
                date=marriage_date,
                place=marriage_place,
                children=children,
            )

        return person


def build_people(cell_data: list[list[Any]], places_manager: PlacesManager) -> dict[int, Person]:
    people = {}
    new_id_start = 99900

    for entry in batched(cell_data, 2):
        if len(entry) != 2:
            continue
        person = Person.from_cells(entry, places_manager=places_manager)
        if not person.id_number:
            person.id_number = new_id_start
            new_id_start += 1
        people[person.id_number] = person

    return people
