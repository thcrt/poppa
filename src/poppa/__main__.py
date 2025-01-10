import typer
import rich


app = typer.Typer(pretty_exceptions_enable=False)
stdout = rich.console.Console()
stderr = rich.console.Console(stderr=True)


@app.command()
def parse(file: str) -> None:
    from poppa import load_data

    people, families = load_data(file)

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
            person["id"],
            person["first"],
            person["last"],
            person["birth_date"],
            person["birth_place"],
            person["death_date"],
            person["death_place"],
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
            family["partner1"],
            family["partner2"],
            family["married_date"],
            family["married_place"],
            ", ".join(family["children"]),
        )
    stdout.print(families_table)


if __name__ == "__main__":
    app()
