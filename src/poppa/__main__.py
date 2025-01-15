from enum import StrEnum, auto
from pathlib import Path
from typing import Annotated

import pyexcel  # type: ignore
import typer
from rich.console import Console
from rich.table import Table

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
    file: Annotated[Path, typer.Argument(help="The spreadsheet to parse.")],
    out: Annotated[Path, typer.Argument(help="Where to output the CSV file for Gramps.")],
    places_file: Annotated[
        Path | None, typer.Option(help="A TOML file detailing place names for parsing.")
    ] = None,
    skip: Annotated[
        int, typer.Option(help="How many rows from the start of the document to skip.")
    ] = 0,
    source: Annotated[
        str | None, typer.Option(help="The title of the source to which data will be attributed.")
    ] = None,
    quiet: Annotated[
        bool, typer.Option(help="Whether to skip printing a table summary.")
    ] = False,
) -> None:
    """Parse an ODS spreadsheet into a Gramps-formatted CSV file."""
    from poppa.export import export
    from poppa.families import build_families
    from poppa.people import build_people
    from poppa.places import PlacesManager

    data = pyexcel.get_array(file_name=str(file))[skip:]
    places_manager = PlacesManager(places_file)

    people = build_people(data, places_manager)
    families, people = build_families(people)

    people_table = Table(
        "ID",
        "First",
        "Nick",
        "Last",
        "Gender",
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
            person.gender,
            person.birth_date,
            person.birth_place,
            person.death_date,
            person.death_place,
        )
    if not quiet:
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
    if not quiet:
        stdout.print(families_table)

    with out.open("w+") as f:
        written = export(f, people, families, places_manager, source)

    if not quiet:
        stdout.rule(style="bold white")
        stdout.rule(style="bold white")

    export_table = Table("Kind", "Quantity", title="Records exported")
    for record_type, number_exported in written.items():
        export_table.add_row(record_type.title(), str(number_exported))
    if not quiet:
        stdout.print(export_table)


if __name__ == "__main__":
    app()
