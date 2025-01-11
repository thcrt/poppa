from itertools import batched

import pyexcel  # type: ignore

from .families import Family, build_families
from .people import Person


def load_data(filename: str) -> tuple[dict[int, Person], list[Family]]:
    data = pyexcel.get_array(file_name=filename)

    people = {}
    new_id_start = 99900

    for entry in batched(data, 2):
        if len(entry) < 2:
            continue
        person = Person.from_cells(entry)
        if not person.id_number:
            person.id_number = new_id_start
            new_id_start += 1
        people[person.id_number] = person

    families = build_families(people, new_id_start)

    return people, families
