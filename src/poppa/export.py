import csv
import io

from .families import Family
from .people import Person
from .places import PlacesManager

PLACE_COLUMNS = [
    "place",
    "name",
    "type",
    "latitude",
    "longitude",
    "enclosed_by",
]

PERSON_COLUMNS = [
    "person",
    "first_name",
    "last_name",
    "gender",
    "source",
    "birthdate",
    "birthplaceid",
    "birthsource",
    "deathdate",
    "deathplaceid",
    "deathsource",
    "note",
]

FAMILY_COLUMNS = [
    "marriage",
    "parent1",
    "parent2",
    "date",
    "placeid",
    "source",
]

CHILDREN_COLUMNS = [
    "family",
    "child",
    "source",
]


def write_places(places_manager: PlacesManager, buf: io.TextIOBase) -> int:
    written = 0
    writer = csv.DictWriter(buf, fieldnames=PLACE_COLUMNS)
    writer.writeheader()
    for place_id, place in places_manager.places.items():
        lat, long = place.coords.split(", ")
        writer.writerow(
            {
                "place": f"place_{place_id}",
                "name": place.name,
                "type": place.type,
                "latitude": lat,
                "longitude": long,
                "enclosed_by": f"place_{place.enclosed_by}" if place.enclosed_by else None,
            }
        )
        written += 1
    return written


def write_people(people: dict[int, Person], source: str | None, buf: io.TextIOBase) -> int:
    written = 0
    writer = csv.DictWriter(buf, fieldnames=PERSON_COLUMNS)
    writer.writeheader()
    for person_id, person in people.items():
        notes = person.notes
        if person.nick is not None:
            notes = f"{notes}  NICKNAME: {person.nick}"
        writer.writerow(
            {
                "person": f"person_{person_id}",
                "first_name": person.first,
                "last_name": person.last,
                "gender": person.gender,
                "source": source,
                "birthdate": person.birth_date,
                "birthplaceid": f"place_{person.birth_place.id}" if person.birth_place else None,
                "birthsource": source if person.birth_date or person.birth_place else None,
                "deathdate": person.death_date,
                "deathplaceid": f"place_{person.death_place.id}" if person.death_place else None,
                "deathsource": source if person.death_date or person.death_place else None,
                "note": notes,
            }
        )
        written += 1
    return written


def write_marriages(families: list[Family], source: str | None, buf: io.TextIOBase) -> int:
    written = 0
    writer = csv.DictWriter(buf, fieldnames=FAMILY_COLUMNS)
    writer.writeheader()
    for family_id, family in enumerate(families):
        writer.writerow(
            {
                "marriage": f"family_{family_id}",
                "parent1": f"person_{family.partner1.id_number}" if family.partner1 else None,
                "parent2": f"person_{family.partner2.id_number}" if family.partner2 else None,
                "date": family.married_date,
                "placeid": f"place_{family.married_place.id}" if family.married_place else None,
                "source": source,
            }
        )
        written += 1
    return written


def write_children(families: list[Family], source: str | None, buf: io.TextIOBase) -> int:
    written = 0
    writer = csv.DictWriter(buf, fieldnames=CHILDREN_COLUMNS)
    writer.writeheader()
    for family_id, family in enumerate(families):
        for child in family.children:
            writer.writerow(
                {
                    "family": f"family_{family_id}",
                    "child": f"person_{child.id_number}",
                    "source": source,
                }
            )
            written += 1
    return written


def export(
    buf: io.TextIOBase,
    people: dict[int, Person],
    families: list[Family],
    places_manager: PlacesManager,
    source: str | None,
) -> dict[str, int]:
    written = {}

    written["places"] = write_places(places_manager, buf)
    buf.write("\n")
    written["people"] = write_people(people, source, buf)
    buf.write("\n")
    written["marriages"] = write_marriages(families, source, buf)
    buf.write("\n")
    written["children"] = write_children(families, source, buf)

    return written
