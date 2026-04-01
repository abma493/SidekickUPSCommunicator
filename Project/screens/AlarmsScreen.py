import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from textual.screen import ModalScreen
from textual.app import ComposeResult, on
from textual.widgets import Static, Button
from textual.containers import Vertical, ScrollableContainer, Horizontal


class AlarmsScreen(ModalScreen):

    CSS_PATH = "../assets/alarms_screen.css"

    def __init__(self, alarms: list):
        super().__init__()
        self._alarms = alarms

    def compose(self) -> ComposeResult:
        with Vertical(id="alarms-modal"):
            yield Static("=== Active Alarms ===", id="alarms-title")
            with ScrollableContainer(id="alarms-list"):
                if self._alarms:
                    for alarm in self._alarms:
                        yield Static(str(alarm), classes="alarm-entry")
                else:
                    yield Static("No active alarms.", id="no-alarms-label")
            with Horizontal(id="alarms-buttons"):
                yield Button("Return", id="alarms-return-button")

    def on_mount(self) -> None:
        self.query_one("#alarms-return-button", Button).focus()

    @on(Button.Pressed, "#alarms-return-button")
    def on_return_pressed(self) -> None:
        self.dismiss()
