import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from textual.screen import ModalScreen
from textual import work
from textual.containers import Horizontal, Container, Vertical
from textual.widgets import Static, Input, Button
from textual.app import ComposeResult, on
from advancedUtils import *
from .ParametersScreen import ParametersScreen

DEFAULT_PARAMS = {
    "below_batt":     False,
    "batt_threshold": 70,
    "audible_alm":    False,
    "below_load":     False,
    "load_threshold": 0,
    "batt_stat":      "Any",
}

class GenerateReport(ModalScreen):

    CSS_PATH = "../assets/generate_report_screen.css"
    BINDINGS = [
        ("up",    "focus_previous"),
        ("down",  "focus_next"),
        ("left",  "focus_previous"),
        ("right", "focus_next"),
    ]

    def on_mount(self) -> None:
        self._params = DEFAULT_PARAMS.copy()

    def compose(self) -> ComposeResult:
        with Vertical(id="report-screen"):
            with Horizontal(id="query-container"):
                yield Static("Path:", id="path-label")
                yield Input(placeholder="path to batch file", id="path-field")
                yield Button("Run Report", id="rsearch-button")
            with Container(id="control-container"):
                yield Static("=== STATUS ===", id="status-line")
                yield Static("Ready", id="status-message")
                with Horizontal(id="btn-row"):
                    yield Button("Return", id="return-button")
                    yield Button("Parameters", id="parameters-button")

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    @on(Button.Pressed, "#return-button")
    def on_return_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#parameters-button")
    def on_parameters_pressed(self) -> None:
        def apply_params(result):
            if result is not None:
                self._params = result
        self.app.push_screen(ParametersScreen(self._params), apply_params)

    @on(Button.Pressed, "#rsearch-button")
    def on_search_pressed(self) -> None:
        path = self.query_one("#path-field").value
        stat_msg = self.query_one("#status-message")
        test_path = os.path.abspath(path)
        if not os.path.exists(test_path):
            stat_msg.update("File not found.")
        else:
            stat_msg.update("Generating report...")
            self.query_one("#return-button", Button).disabled = True
            self.query_one("#rsearch-button", Button).disabled = True
            self.generate_report(test_path)

    @work(thread=True)
    def generate_report(self, test_path: str) -> None:
        asyncio.run(run_report(
            below_batt=self._params["below_batt"],
            batt_threshold=self._params["batt_threshold"],
            audible_alm=self._params["audible_alm"],
            below_load=self._params["below_load"],
            load_threshold=self._params["load_threshold"],
            batt_stat=self._params["batt_stat"],
            ip_list=test_path,
        ))
        self.app.call_from_thread(self.query_one("#status-message").update, "Report complete.")
        self.app.call_from_thread(setattr, self.query_one("#return-button", Button), "disabled", False)
        self.app.call_from_thread(setattr, self.query_one("#rsearch-button", Button), "disabled", False)
