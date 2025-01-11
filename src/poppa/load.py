from itertools import batched
from pathlib import Path

import pyexcel  # type: ignore

from .families import Family, build_families
from .people import Person
from .places import PlacesManager


def load_data(
    file: Path, places_file: Path | None = None
) -> tuple[dict[int, Person], list[Family]]:
    data = pyexcel.get_array(file_name=str(file))
    places_manager = PlacesManager(places_file)

    people = {}
    new_id_start = 99900

    for entry in batched(data, 2):
        if len(entry) < 2:
            continue
        person = Person.from_cells(entry, places_manager=places_manager)
        if not person.id_number:
            person.id_number = new_id_start
            new_id_start += 1
        people[person.id_number] = person

    families = build_families(people, new_id_start)

    return people, families
