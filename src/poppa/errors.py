import re
import rich
from .__main__ import stderr


class PoppaBaseError(Exception):
    pass


class UnknownPlaceNameError(PoppaBaseError):
    def __init__(self, place_name: str):
        super().__init__(place_name)
        self.place_name = place_name


def show_error(title: str, msg: str) -> None:
    msg = re.sub(r"#(\d+)", r"[dim]#[/dim][bold]\g<1>[/bold]", msg)
    stderr.print(
        rich.panel.Panel(
            msg,
            title=rich.text.Text(text=title, style="bold red"),
            expand=False,
            border_style="red",
        )
    )
    raise SystemExit
