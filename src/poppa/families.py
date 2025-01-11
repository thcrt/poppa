from dataclasses import dataclass, field

from .dates import Date
from .errors import show_error
from .people import Person
from .places import PlacesManager


@dataclass
class Family:
    partner1: Person | None = None
    partner2: Person | None = None
    married_date: Date | None = None
    married_place: PlacesManager.Place | None = None
    children: list[Person] = field(default_factory=list)


def build_families(people: dict[int, Person], new_id_start: int) -> list[Family]:
    families: list[Family] = []

    for person in people.values():
        for family in families:
            if person in (family.partner1, family.partner2):
                # Person was already processed as the spouse of a previous person
                continue

        if person.marriage:
            spouse = None

            if person.marriage.spouse:
                if person.marriage.spouse not in people:
                    show_error(
                        "Spouse ID nonexistent",
                        f"#{person.id_number} lists #{person.marriage.spouse} as their spouse, but "
                        f"that ID doesn't exist! \nMake sure the ID number is correct, and create "
                        f"an entry for them if necessary.",
                    )

                spouse = people[person.marriage.spouse]

                # We check to make sure the details of the marriage match between both partners.
                # Note that, if someone remarried or had children outside of wedlock, we'll probably
                # throw an error here. This is okay, because this is relatively uncommon, so we can
                # just edit the source spreadsheet by hand to only reference one marriage, and add
                # a note to the affected people reminding us to manually add the second marriage to
                # Gramps after importing.
                if spouse.marriage is None:
                    show_error(
                        "Marriage not reciprocated",
                        f"#{person.id_number} lists #{spouse.id_number} as their spouse, but "
                        f"#{spouse.id_number} doesn't list them as their spouse in return, instead "
                        f"listing nobody!",
                    )
                    # show_error() exits anyway, but we explicitly exit here to satisfy the type
                    # checker that `spouse` can no longer be `None`.
                    raise SystemExit
                if spouse.marriage.spouse != person.id_number:
                    show_error(
                        "Marriage not reciprocated",
                        f"#{person.id_number} lists #{spouse.id_number} as their spouse, but "
                        f"#{spouse.id_number} doesn't list them as their spouse in return, instead "
                        f"listing `{spouse.marriage.spouse}`!",
                    )
                if spouse.marriage.date != person.marriage.date:
                    show_error(
                        "Marriage dates don't match",
                        f"Marriage dates for #{person.id_number} (`{person.marriage.date}`) and "
                        f"#{spouse.id_number} (`{spouse.marriage.date}`) don't match!",
                    )
                if spouse.marriage.place != person.marriage.place:
                    show_error(
                        "Marriage places don't match",
                        f"Marriage places for #{person.id_number} (`{person.marriage.place}`) and "
                        f"#{spouse.id_number} (`{spouse.marriage.place}`) don't match!",
                    )
                if spouse.marriage.children != person.marriage.children:
                    show_error(
                        "Children don't match",
                        f"Children for #{person.id_number} and #{spouse.id_number} don't match! \n"
                        f"#{person.id_number}'s children are: {person.marriage.children} \n"
                        f"#{spouse.id_number}'s children are: {spouse.marriage.children}",
                    )

            family = Family(married_date=person.marriage.date, married_place=person.marriage.place)

            # Parents are listed father-first. Similarly, in Gramps, the first partner in a family
            # is typically the father. This means that, if any children are listed, we can make a
            # pretty good guess about who is whom. Otherwise, we've just got a 50/50 shot, but it
            # doesn't matter too much if we're wrong.
            person_is_partner1 = False

            for child_id_number in person.marriage.children:
                if child_id_number not in people:
                    show_error(
                        "Child ID nonexistent",
                        f"#{person.id_number} lists #{child_id_number} as a child, but that ID "
                        f"doesn't exist! \nMake sure the ID number is correct, and create an entry "
                        f"for them if necessary.",
                    )
                child = people[child_id_number]

                parents = (person.id_number, spouse.id_number) if spouse else (person.id_number,)
                for parent in parents:
                    if parent not in child.parents:
                        show_error(
                            "Child missing parent",
                            f"#{child.id_number} is listed as the child of #{parent}, but doesn't "
                            f"list them as their parent! If #{child.id_number} is really the child "
                            f"of #{parent}, add `{parent}` to their parents entry. Otherwise, "
                            f"remove #{child.id_number}'s ID from #{parent}'s children entry.",
                        )

                if spouse is None and None not in child.parents:
                    show_error(
                        "Child has unknown parent",
                        f"#{child.id_number} lists #{person.id_number}, who is unmarried as their "
                        f"parent, but also lists a second parent. If #{person.id_number} is "
                        f"married, make sure that's reflected correctly. Otherwise, check the "
                        f"parents entry for #{child.id_number}.",
                    )

                if child.parents == (person.id_number, spouse.id_number if spouse else None):
                    person_is_partner1 = True

                family.children.append(child)

            if person_is_partner1:
                family.partner1 = person
                family.partner2 = spouse
            else:
                family.partner1 = spouse
                family.partner2 = person

            families.append(family)

    return families
