from pathlib import Path

import rich
import typer

app = typer.Typer(pretty_exceptions_enable=False)
stdout = rich.console.Console()
stderr = rich.console.Console(stderr=True)


@app.command()
def parse(file: Path, places_file: Path | None = None) -> None:
    from poppa import load_data

    people, families = load_data(file, places_file=places_file)

    people_table = rich.table.Table(
        "ID",
        "First",
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
            person.last,
            person.birth_date,
            person.birth_place,
            person.death_date,
            person.death_place,
        )
    stdout.print(people_table)

    families_table = rich.table.Table(
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


if __name__ == "__main__":
    app()
