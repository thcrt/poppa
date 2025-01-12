from enum import StrEnum, auto
from pathlib import Path

import pyexcel  # type: ignore
from rich.table import Table
from rich.console import Console
import typer

from .errors import ErrorManager

app = typer.Typer(pretty_exceptions_enable=False)
stdout = Console()
stderr = Console(stderr=True)
error_manager = ErrorManager(Path("./choices.poppa.csv"), stdout, stderr)


class DisplayFormat(StrEnum):
    smart = auto()
    gramps = auto()
    hidden = auto()


@app.command()
def parse(
    file: Path = typer.Argument(help="The spreadsheet to parse."),
    out: Path = typer.Argument(help="Where to output the CSV file for Gramps."),
    places_file: Path | None = typer.Option(
        None, help="A TOML file detailing place names for parsing."
    ),
) -> None:
    """Parse an ODS spreadsheet into a Gramps-formatted CSV file."""
    from poppa.export import export
    from poppa.families import build_families
    from poppa.people import build_people
    from poppa.places import PlacesManager

    data = pyexcel.get_array(file_name=str(file))
    places_manager = PlacesManager(places_file)

    people = build_people(data, places_manager)
    families = build_families(people)

    people_table = Table(
        "ID",
        "First",
        "Nick",
        "Last",
        "Birth date",
        "Birth place",
        "Death date",
        "Death place",
        title="People",
    )
    for person in people.values():
        people_table.add_row(
            str(person.id_number),
            person.first,
            person.nick,
            person.last,
            person.birth_date,
            person.birth_place,
            person.death_date,
            person.death_place,
        )
    stdout.print(people_table)

    families_table = Table(
        "Partner 1",
        "Partner 2",
        "Married date",
        "Married place",
        "Children",
        title="Families",
    )
    for family in families:
        families_table.add_row(
            str(family.partner1.id_number) if family.partner1 else "",
            str(family.partner2.id_number) if family.partner2 else "",
            family.married_date,
            family.married_place,
            ", ".join(str(child.id_number) for child in family.children),
        )
    stdout.print(families_table)

    with out.open("w+") as f:
        written = export(f, people, families, places_manager)

    stdout.rule(style="bold white")
    stdout.rule(style="bold white")

    export_table = Table(
        "Kind",
        "Quantity",
        title="Records exported"
    )
    for record_type, number_exported in written.items():
        export_table.add_row(
            record_type.title(),
            str(number_exported)
        )
    stdout.print(export_table)

if __name__ == "__main__":
    app()
