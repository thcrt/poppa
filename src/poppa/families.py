from dataclasses import dataclass, field

from .__main__ import error_manager
from .dates import Date
from .people import Marriage, Person
from .places import PlacesManager


@dataclass
class Family:
    partner1: Person | None = None
    partner2: Person | None = None
    married_date: Date | None = None
    married_place: PlacesManager.Place | None = None
    children: list[Person] = field(default_factory=list)


def build_families(people: dict[int, Person]) -> list[Family]:
    families: list[Family] = []

    for person in people.values():
        already_processed = False
        for family in families:
            if (family.partner1 and family.partner1.id_number == person.id_number) or (
                family.partner2 and family.partner2.id_number == person.id_number
            ):
                # Person was already processed as the spouse of a previous person
                already_processed = True
        if already_processed:
            continue

        if person.marriage:
            spouse = None

            if person.marriage.spouse:
                if person.marriage.spouse not in people:
                    error_manager.show_error(
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
                if spouse.marriage is None or spouse.marriage.spouse is None:
                    match error_manager.show_warning(
                        "Marriage not reciprocated",
                        f"#{person.id_number} lists #{spouse.id_number} as their spouse, but "
                        f"#{spouse.id_number} doesn't list them as their spouse in return, instead "
                        f"listing nobody!",
                        {
                            "a": f"Add #{person.id_number} as #{spouse.id_number}'s spouse",
                        },
                        f"marriage_recip.{person.id_number}.{spouse.id_number}",
                    ):
                        case "a":
                            if spouse.marriage is None:
                                spouse.marriage = Marriage()
                            spouse.marriage.spouse = person.id_number
                assert isinstance(spouse.marriage, Marriage)
                if spouse.marriage.spouse != person.id_number:
                    error_manager.show_error(
                        "Marriage not reciprocated",
                        f"#{person.id_number} lists #{spouse.id_number} as their spouse, but "
                        f"#{spouse.id_number} doesn't list them as their spouse in return, instead "
                        f"listing `{spouse.marriage.spouse}`!",
                    )
                if spouse.marriage.date != person.marriage.date:
                    match error_manager.show_warning(
                        "Marriage dates don't match",
                        f"Marriage dates for #{person.id_number} (`{person.marriage.date}`) and "
                        f"#{spouse.id_number} (`{spouse.marriage.date}`) don't match!",
                        {
                            "a": f"Use `{person.marriage.date}` for both spouses",
                            "d": f"Use `{spouse.marriage.date}` for both spouses",
                        },
                        f"marriage_date.{person.id_number}.{person.marriage.date}."
                        f"{spouse.id_number}.{spouse.marriage.date}",
                    ):
                        case "a":
                            spouse.marriage.date = person.marriage.date
                        case "d":
                            person.marriage.date = spouse.marriage.date
                if spouse.marriage.place != person.marriage.place:
                    match error_manager.show_warning(
                        "Marriage places don't match",
                        f"Marriage places for #{person.id_number} (`{person.marriage.place}`) and "
                        f"#{spouse.id_number} (`{spouse.marriage.place}`) don't match!",
                        {
                            "a": f"Use `{person.marriage.place}` for both spouses",
                            "d": f"Use `{spouse.marriage.place}` for both spouses",
                        },
                        f"marriage_place.{person.id_number}.{person.marriage.place}."
                        f"{spouse.id_number}.{spouse.marriage.place}",
                    ):
                        case "a":
                            spouse.marriage.place = person.marriage.place
                        case "d":
                            person.marriage.place = spouse.marriage.place
                if spouse.marriage.children != person.marriage.children:
                    if person.marriage.children == []:
                        match error_manager.show_warning(
                            "One partner missing children",
                            f"#{spouse.id_number} has the children {spouse.marriage.children}, but "
                            f"their spouse #{person.id_number} has no children listed!",
                            {
                                "a": f"Add #{spouse.id_number}'s children to #{person.id_number}",
                            },
                            f"missing_children_p.{person.id_number}.{spouse.id_number}."
                            f"{'.'.join(str(child_id) for child_id in spouse.marriage.children)}",
                        ):
                            case "a":
                                person.marriage.children = spouse.marriage.children
                    elif spouse.marriage.children == []:
                        match error_manager.show_warning(
                            "One partner missing children",
                            f"#{person.id_number} has the children {person.marriage.children}, but "
                            f"their spouse #{spouse.id_number} has no children listed!",
                            {
                                "a": f"Add #{person.id_number}'s children to #{spouse.id_number}",
                            },
                            f"missing_children_s.{person.id_number}.{spouse.id_number}."
                            f"{'.'.join(str(child_id) for child_id in person.marriage.children)}",
                        ):
                            case "a":
                                spouse.marriage.children = person.marriage.children
                            case "q":
                                raise SystemExit
                    else:
                        error_manager.show_error(
                            "Children don't match",
                            f"Children for #{person.id_number} and #{spouse.id_number} don't "
                            f"match! \n"
                            f"#{person.id_number}'s children are: {person.marriage.children} \n"
                            f"#{spouse.id_number}'s children are: {spouse.marriage.children}",
                        )

            family = Family(married_date=person.marriage.date, married_place=person.marriage.place)

            # Parents are listed father-first. Similarly, in Gramps, the first partner in a family
            # is typically the father. This means that, if any children are listed, we can make a
            # pretty good guess about who is whom. Otherwise, we've just got a 50/50 shot, but it
            # doesn't matter too much if we're wrong.
            person_is_partner1 = True

            for child_id_number in person.marriage.children:
                if child_id_number not in people:
                    error_manager.show_error(
                        "Child ID nonexistent",
                        f"#{person.id_number} lists #{child_id_number} as a child, but that ID "
                        f"doesn't exist! \nMake sure the ID number is correct, and create an entry "
                        f"for them if necessary.",
                    )
                child = people[child_id_number]

                if spouse is None:
                    spouse = Person()

                match child.parents:
                    case (spouse.id_number, person.id_number):
                        person_is_partner1 = False
                    case (person.id_number, spouse.id_number):
                        person_is_partner1 = True
                    case (None, person.id_number) | (person.id_number, None):
                        match error_manager.show_warning(
                            "Child missing one parent",
                            f"#{child.id_number} is listed as the child of #{spouse.id_number}, "
                            f"but they do not list #{spouse.id_number} as a parent.",
                            {
                                "a": f"Add #{spouse.id_number} to #{child.id_number}'s parents "
                                f"entry",
                            },
                            f"missing_parent_s.{child.id_number}.{person.id_number}.{spouse.id_number}",
                        ):
                            case "a":
                                child.parents[child.parents.index(None)] = spouse.id_number
                    case (None, spouse.id_number) | (spouse.id_number, None):
                        match error_manager.show_warning(
                            "Child missing one parent",
                            f"#{child.id_number} is listed as the child of #{person.id_number}, "
                            f"but they do not list #{person.id_number} as a parent.",
                            {
                                "a": f"Add #{person.id_number} to #{child.id_number}'s parents "
                                f"entry",
                            },
                            f"missing_parent_p.{child.id_number}.{person.id_number}.{spouse.id_number}",
                        ):
                            case "a":
                                child.parents[child.parents.index(None)] = spouse.id_number
                    case (None, None):
                        match error_manager.show_warning(
                            "Child missing both parents",
                            f"#{child.id_number} is listed as the child of #{person.id_number} and "
                            f"#{spouse.id_number}. However, they do not have any parents listed.",
                            {
                                "a": f"Add #{person.id_number} and #{spouse.id_number} to "
                                f"#{child.id_number}'s parents entry",
                                "d": f"Add #{spouse.id_number} and #{person.id_number} to "
                                f"#{child.id_number}'s parents entry",
                            },
                            f"missing_parent_b.{child.id_number}.{person.id_number}.{spouse.id_number}",
                        ):
                            case "a":
                                child.parents = [person.id_number, spouse.id_number]
                            case "d":
                                child.parents = [spouse.id_number, person.id_number]

                family.children.append(child)

            if person_is_partner1:
                family.partner1 = person
                family.partner2 = spouse
            else:
                family.partner1 = spouse
                family.partner2 = person

            families.append(family)

    return families
