import importlib.resources
import re
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path
from tomllib import loads

from . import errors


class PlacesManager:
    @dataclass
    class Place:
        name: str
        pattern: str | None
        type: str
        coords: str
        enclosed_by: str | None
        uncertain: bool = False

        def __str__(self) -> str:
            return f"{self.name}" + (" [???]" if self.uncertain else "")

        def __rich__(self) -> str:
            return self.name.split(", ")[0]

    places: dict[str, Place] = {}

    def __init__(self, file: Path | Traversable | None):
        if file is None:
            file = importlib.resources.files().joinpath("places.toml")

        place_data = loads(file.read_text())
        for place_id, info in place_data.items():
            self.places[place_id] = self.Place(
                name=info["name"],
                pattern=info.get("pattern", None),
                type=info["type"],
                coords=info["coords"],
                enclosed_by=info.get("enclosed_by"),
            )

    def from_entry(self, entry: str | None) -> Place | None:
        if entry is None:
            return None
        for place in self.places.values():
            if place.pattern and re.fullmatch(place.pattern, entry.strip(" .?")):
                return place
        # If we didn't return yet, we didn't match a pattern, so we raise an error.
        raise errors.UnknownPlaceNameError
