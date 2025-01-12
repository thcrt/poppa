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
        id: str
        name: str
        pattern: str | None
        type: str
        coords: str
        enclosed_by: str | None

        def __str__(self) -> str:
            return self.name

        def __rich__(self) -> str:
            return self.name

    places: dict[str, Place] = {}

    def __init__(self, file: Path | Traversable | None):
        if file is None:
            file = importlib.resources.files().joinpath("places.toml")

        place_data = loads(file.read_text())
        for place_id, info in place_data.items():
            self.places[place_id] = self.Place(
                id=place_id,
                name=info["name"],
                pattern=info.get("pattern", None),
                type=info["type"],
                coords=info["coords"],
                enclosed_by=info.get("enclosed_by"),
            )

    def from_entry(self, entry: str) -> Place | None:
        entry = entry.strip(" .?")
        if entry == "":
            return None
        for place in self.places.values():
            if place.pattern and re.fullmatch(place.pattern, entry):
                return place
        # If we didn't return yet, we didn't match a pattern, so we raise an error.
        raise errors.UnknownPlaceNameError
