import re

import rich

from .__main__ import stderr


class PoppaBaseError(Exception):
    pass


class UnknownPlaceNameError(PoppaBaseError):
    pass


class InvalidDateError(PoppaBaseError):
    pass


class MultipleReferencesError(PoppaBaseError):
    pass


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
