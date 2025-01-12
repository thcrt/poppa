import csv
import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text


class PoppaBaseError(Exception):
    pass


class UnknownPlaceNameError(PoppaBaseError):
    pass


class InvalidDateError(PoppaBaseError):
    pass


class MultipleReferencesError(PoppaBaseError):
    pass


class ErrorManager:
    save_file: Path
    stdout: Console
    stderr: Console

    def __init__(self, save_file: Path, stdout: Console, stderr: Console):
        self.save_file = save_file
        self.stdout = stdout
        self.stderr = stderr

    def _format_message(self, msg: str) -> str:
        return re.sub(r"#(\d+)", r"[dim]#[/dim][bold]\g<1>[/bold]", msg)

    def show_error(self, title: str, msg: str) -> None:
        msg = self._format_message(msg)
        self.stderr.print(
            Panel(
                msg,
                title=Text(text=title, style="bold red"),
                expand=False,
                border_style="red",
            )
        )
        raise SystemExit

    def _save_response(self, save_key: str, response: str, mode: str = "a") -> None:
        try:
            with self.save_file.open(mode) as f:
                writer = csv.writer(f)
                writer.writerow([save_key, response])
        except FileNotFoundError:
            if mode == "w+":
                raise
            else:
                self._save_response(save_key, response, mode="w+")

    def _get_response(self, save_key: str) -> str | None:
        try:
            with self.save_file.open("r") as f:
                reader = csv.reader(f)
                for line in reader:
                    if line[0] == save_key:
                        return line[1]
            return None
        except FileNotFoundError:
            return None

    def show_warning(
        self, title: str, msg: str, options: dict[str, str], save_key: str, quittable: bool = True
    ) -> str:
        previous_response = self._get_response(save_key)
        if previous_response:
            return previous_response

        msg = self._format_message(msg)
        msg += "\n"
        if quittable:
            options["q"] = "Quit"
        for key, option in options.items():
            msg += f"\n[bold]\\[{key}][/bold] {option}"
        self.stdout.print(
            Panel(
                msg,
                title=Text(text=title, style="bold yellow"),
                expand=False,
                border_style="yellow",
            )
        )

        response = Prompt.ask(choices=options.keys())
        if quittable and response == "q":
            raise SystemExit
        self._save_response(save_key, response)
        return response
