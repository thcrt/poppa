from . import errors

from itertools import batched
import re
from typing import Optional, Any

import pyexcel  # type: ignore


PLACE_PATTERNS = {
    "Hamilton, Waikato, New Zealand": r"^[Hh]am(?:ilton)? ?(?:N[Zz])?$",
    "Waihi, Waikati, New Zealand": r"^Waihi ?NZ$",
    "Te Rapa, Hamilton, Waikato, New Zealand": r"^Te Rapa(?: NZ)?$",
    "Cambridge, Waikato, New Zealand": r"^[Cc]a?m?br?i?dge ?N[Zz]$",
    "Tairua, Waikato, New Zealand": r"^Tairua$",
    "Matamata, Waikato, New Zealand": r"^Matamata ?NZ$",
    "Te Rore, Waikato, New Zealand": r"^Te Rore ?NZ$",
    "Morrinsville, Waikato, New Zealand": r"^Morr?insvill?[e-]? ?N?Z?$",
    "Ngāruawāhia, Waikato, New Zealand": r"^Ngaruawa?hia ?(?:NZ)?$",
    "Opito Bay, Waikato, New Zealand": r"^Opito Bay NZ$",
    "Christchurch, Canterbury, New Zealand": r"^Ch(?:rist)?(?:ch|Ch)(?:urch)? ?NZ$",
    "Templeton, Canterbury, New Zealand": r"^Templet(?:on)? ?NZ$",
    "Sefton, Canterbury, New Zealand": r"^Sefton NZ$",
    "Waimate, Canterbury, New Zealand": r"^Waimate ?[NM]Z$",
    "Raetihi, Manawatū-Whanganui, New Zealand": r"^Raetihi ?NZ$",
    "Taumarunui, Manawatū-Whanganui, New Zealand": r"^Taumara(?:nui)? ?NZ$",
    "Ōwhango, Manawatū-Whanganui, New Zealand": r"^Owa?ha?n?go ?NZ$",
    "Whangārei, Northland, New Zealand": r"^Whangar?ei ?NZ$",
    "Moerewa, Northland, New Zealand": r"^mo[ew]rewa ?NZ$",
    "Kaponga, Taranaki, New Zealand": r"^Kaponga ?NZ$",
    "New Plymouth, Taranaki, New Zealand": r"^N(?:ew)? Plymouth ?NZ$",
    "Auckland, New Zealand": r"^Auck(?:land)? ?(?:N[Zz])?$",
    "Waitākere, Auckland, New Zealand": r"^Waitakere NZ$",
    "Henderson, Auckland, New Zealand": r"^Henderson ?N[Zz]$",
    "Takapuna, Auckland, New Zealand": r"^Takapuna ?NZ$",
    "Middlemore, Auckland, New Zealand": r"^Middlemore$",
    "Papakura, Auckland, New Zealand": r"^Papakura ?NZ$",
    "Orewa, Auckland, New Zealand": r"^Orewa NZ$",
    "Pitt Street, Auckland, New Zealand": r"^Pitt St Auck(?:land)?$",
    "Rotorua, Bay of Plenty, New Zealand": r"^Rotorua(?: NZ)?$",
    "Ōtaki, Greater Wellington, New Zealand": r"^Otaki ?NZ$",
    "Dunedin, Otago, New Zealand": r"^Dunedin NZ$",
    "Australia": r"^Aust(?:ralia)?$",
    "Sydney, New South Wales, Australia": r"^Syd(?:ney)?.? ?A(?:U|ust(?:ralia)?)$",
    "England, UK": r"^Eng(?:land)?$",
    "London, England, UK": r"^London ?E(?:NG|ng)$",
    "Glasgow, Scotland, UK": r"^Glas[cg]ow ?SC$",
    "Londonderry County, Northern Ireland, UK": r"^C Derry ?IRE$",
    "Indonesia": r"^Indonesia$",
    "Cook Islands": r"^Cook Is(?:lands)?$",
    "Aitutaki, Cook Islands": r"^Ai?tutaki ?CI$",
    "Johannesburg, Gauteng, South Africa": r"^Johann?[ea]?sb?u?r?g? ?SA$",
}


def sanitise_place(place_name: str) -> Optional[str]:
    unsure = "?" in place_name

    place_name = place_name.strip(" .?")

    if not place_name:
        return None

    for replacement, pattern in PLACE_PATTERNS.items():
        if re.match(pattern, place_name):
            return f"??? {replacement} ???" if unsure else replacement

    raise errors.UnknownPlaceNameError(place_name)


type Person = dict[str, Optional[str]]


def parse_person(data: tuple[Any, ...]) -> Person:
    person: Person = {}

    person["id"] = str(data[0][0]).strip("# .")
    person["first"] = str(data[1][1]).title()
    person["last"] = str(data[0][1]).title()

    person["parent1"] = str(data[0][3]).strip()
    person["parent2"] = str(data[1][3]).strip()

    try:
        person["birth_date"] = str(data[0][2])
        person["birth_place"] = sanitise_place(str(data[1][2]))
        person["death_date"] = str(data[0][6])
        person["death_place"] = sanitise_place(str(data[1][6]))
    except errors.UnknownPlaceNameError:
        errors.show_error(
            "Unknown place name", f"While handling birth and death of #{person['id']}"
        )

    person["spouse"] = str(data[0][4]).strip()

    # Extract date and place of marriage from the same field
    person["married_date"] = None
    person["married_place"] = None
    marriage = str(data[1][4]).strip(". ?")
    try:
        if marriage:
            # Grab date-ish looking numbers out
            date_match = re.search(r"\d{1,4}(?:[-./]\d{1,4})*", marriage)
            if date_match:
                married_date = date_match.group(0)
                person["married_date"] = married_date
                # Assume the place is just the rest of the field with the date removed
                person["married_place"] = sanitise_place(marriage.replace(married_date, ""))
            else:
                # Since we couldn't find a number, assume it's just the place
                person["married_place"] = sanitise_place(marriage)
    except errors.UnknownPlaceNameError:
        errors.show_error("Unknown place name", f"While handling marriage of #{person['id']}")

    # Children are present in upper and lower rows
    person["children"] = str(data[0][5]) + " " + str(data[1][5])

    person["notes"] = " ".join(cell for cell in (data[0][8:] + data[1][8:]) if cell)

    # Remove empty notes
    for key, value in person.items():
        if value is not None and value.strip() in (
            "never married",
            "no issue",
            "xxx",
            "na",
            "",
        ):
            person[key] = None

    return person


def build_families(people: dict[str, Person]) -> tuple[dict[str, Person], list[dict[str, Any]]]:
    families = []

    for person_id, person in people.items():
        if "spouse" in person:
            # Ensure `spouse` field isn't `None`
            # This method unfortunately means we have to manually add empty ID-only spouse entries
            # for cases where we only know 1 parent and nothing is known about the other, or else
            # we skip them here and then end up complaining later on that they haven't already
            # been listed as a child.
            if not person["spouse"]:
                del people[person_id]["spouse"]
                continue

            # Extract ID from `spouse` field by regex-ing for numbers
            spouse_id_match = re.search(r"\d+", person["spouse"])
            if not spouse_id_match:
                errors.show_error(
                    "Spouse ID not matched",
                    f"#{person_id}'s spouse field isn't empty, but it doesn't contain a recognisable ID number. \n"
                    f"If #{person_id} had a spouse, make sure they have been given an ID number.",
                )
                break  # To satisfy type checker that we won't continue

            # Make sure that ID belongs to a person in the data already
            spouse_id = spouse_id_match.group(0)
            if spouse_id not in people:
                errors.show_error(
                    "Child ID nonexistent",
                    f"#{person_id} lists #{spouse_id} as a spouse, but that ID doesn't exist! \n"
                    f"Make sure #{spouse_id} is the right ID number, and create an entry for them if necessary.",
                )

            spouse = people[spouse_id]

            person_date = (
                person["married_date"]
                if "married_date" in person and person["married_date"]
                else None
            )
            person_place = (
                person["married_place"]
                if "married_place" in person and person["married_place"]
                else None
            )
            person_children = (
                person["children"] if "children" in person and person["children"] else None
            )
            spouse_date = (
                spouse["married_date"]
                if "married_date" in spouse and spouse["married_date"]
                else None
            )
            spouse_place = (
                spouse["married_place"]
                if "married_place" in spouse and spouse["married_place"]
                else None
            )
            spouse_children = (
                spouse["children"] if "children" in spouse and spouse["children"] else None
            )

            # Make sure relationship is reciprocal
            if (
                "spouse" not in spouse
                or spouse["spouse"] is None
                or person_id not in spouse["spouse"]
            ):
                errors.show_error(
                    "Marriage not reciprocated",
                    f"#{person_id} lists #{spouse_id} as their spouse, but #{spouse_id} only lists `{spouse['spouse']}`!",
                )
            if spouse_date != person_date:
                errors.show_error(
                    "Marriage dates don't match",
                    f"Marriage dates for #{person_id} (`{person_date}`) and #{spouse_id} (`{spouse_date}`) don't match!",
                )
            if spouse_place != person_place:
                errors.show_error(
                    "Marriage places don't match",
                    f"Marriage places for #{person_id} (`{person_place}`) and #{spouse_id} (`{spouse_place}`) don't match!",
                )
            # Also check same children
            # Sometimes people have children from other relationships. To make things easier, since this is rare,
            # just move them from the Children cells into a note and add them after importing
            if spouse_children != person_children:
                errors.show_error(
                    "Children don't match",
                    f"#{person_id} and #{spouse_id} are meant to form a family, but they don't have the same children! \n"
                    f"#{person_id}'s children are: `{person_children}` \n"
                    f"#{spouse_id}'s children are: `{spouse_children}`",
                )

            children = []
            if person_children:
                child_id_matches = re.findall(r"\d+", person_children)
                if not child_id_matches:
                    errors.show_error(
                        "Child ID not matched",
                        f"#{person_id}'s children field isn't empty, but it doesn't contain any recognisable ID numbers. \n"
                        f"If #{person_id} had any children, make sure they have been given ID numbers.",
                    )
                for child_id in child_id_matches:
                    if child_id not in people:
                        errors.show_error(
                            "Child ID nonexistent",
                            f"#{person_id} and #{spouse_id} list #{child_id} as a child, but that ID doesn't exist! \n"
                            f"Make sure #{child_id} is the right ID number, and create an entry for them if necessary.",
                        )

                    child = people[child_id]

                    if not (child["parent1"] and child["parent2"]):
                        errors.show_error(
                            "Child missing parents",
                            f"#{child_id} is listed as the child of #{person_id} and #{spouse_id}, but doesn't list both of them as parents! \n"
                            f"At least one of their parent fields is empty. \n"
                            f"Make sure #{person_id} and #{spouse_id} are both listed as parents of #{child_id}.",
                        )
                        break  # To satisfy type checker that we won't continue

                    if person_id in child["parent1"] and spouse_id in child["parent2"]:
                        reverse_parents_order = False
                    elif person_id in child["parent2"] and spouse_id in child["parent1"]:
                        reverse_parents_order = True
                    else:
                        errors.show_error(
                            "Child missing parents",
                            f"#{child_id} is listed as the child of #{person_id} and #{spouse_id}, but doesn't list both of them as parents! \n"
                            f"Currently, #{child_id} lists their parents as being `{child['parent1']}` and `{child['parent2']}`. \n"
                            f"Make sure #{person_id} and #{spouse_id} are both listed as parents of #{child_id}.",
                        )

                    children.append(child_id)

            # Delete the now-redundant fields from both partners
            # Deleting `spouse` from the partner also avoids creating duplicate families
            for field_name in ["spouse", "married_date", "married_place", "children"]:
                if field_name in people[person_id]:
                    del people[person_id][field_name]
                if field_name in people[spouse_id]:
                    del people[spouse_id][field_name]

            for child_id in children:
                del people[child_id]["parent1"]
                del people[child_id]["parent2"]

            families.append(
                {
                    "partner1": person_id if not reverse_parents_order else spouse_id,
                    "partner2": spouse_id if not reverse_parents_order else person_id,
                    "married_date": person_date,
                    "married_place": person_place,
                    "children": children,
                }
            )

    for person_id, person in people.items():
        # Check to make sure there aren't any people with parents we missed
        # This could happen if someone has parents listed but isn't listed as a child of anyone
        # (because the parents don't have their own entries)
        parent = None
        if "parent1" in person and person["parent1"]:
            parent = person["parent1"]
        elif "parent2" in person and person["parent2"]:
            parent = person["parent2"]

        if parent:
            errors.show_error(
                "Parents missing child",
                f"#{person_id} lists `{parent}` as their parent, but is not listed as a child of any parent! \n"
                f"Make sure `{parent}` contains the ID of an existing parent, and that parent lists #{person_id} as a child.",
            )

        # Ensure all redundant fields are gone, even from people who are single
        for field_name in [
            "spouse",
            "married_date",
            "married_place",
            "children",
            "parent1",
            "parent2",
        ]:
            if field_name in person:
                del people[person_id][field_name]

    return people, families


def load_data(filename: str) -> tuple[dict[str, Person], list[dict[str, Any]]]:
    people = {}

    data = pyexcel.get_array(file_name=filename)

    for entry in batched(data, 2):
        if len(entry) < 2:
            continue
        person = parse_person(entry)
        if not person["id"]:
            # This will never happen but it makes the type checker happy
            continue
        people[person["id"]] = person

    people, families = build_families(people)

    return people, families
