import re
from dataclasses import dataclass
from typing import Self

from . import errors

PATTERNS = {
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


@dataclass
class Place:
    name: str
    uncertain: bool = False

    @classmethod
    def from_entry(cls, entry: str | None) -> Self | None:
        if entry is None:
            return None
        place = None
        for name, pattern in PATTERNS.items():
            if re.fullmatch(pattern, entry.strip(" .?")):
                place = cls(name, uncertain=("?" in entry))
                break
        else:
            # If `break` wasn't called, so we didn't match a pattern, raise an error.
            raise errors.UnknownPlaceNameError
        return place

    def __str__(self) -> str:
        return f"{self.name}" + (" [???]" if self.uncertain else "")

    def __rich__(self) -> str:
        return self.name.split(", ")[0]
