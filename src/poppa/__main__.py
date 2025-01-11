from enum import StrEnum, auto
from pathlib import Path

import pyexcel  # type: ignore
import rich
import rich.table
import typer

app = typer.Typer(pretty_exceptions_enable=False)
stdout = rich.console.Console()
stderr = rich.console.Console(stderr=True)


class DisplayFormat(StrEnum):
    smart = auto()
    gramps = auto()
    hidden = auto()


@app.command()
def parse(file: Path, out: Path, places_file: Path | None = None) -> None:
    from poppa.export import export
    from poppa.families import build_families
    from poppa.people import build_people
    from poppa.places import PlacesManager

    data = pyexcel.get_array(file_name=str(file))
    places_manager = PlacesManager(places_file)

    people = build_people(data, places_manager)
    families = build_families(people)

    with out.open("w+") as f:
        written = export(f, people, families, places_manager)

    print("Done exporting.")
    for label, stat in written.items():
        print(f"  - {label.title()}: {stat}")


if __name__ == "__main__":
    app()
