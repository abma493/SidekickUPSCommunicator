import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from textual.screen import ModalScreen
from textual.app import ComposeResult, on
from textual.widgets import Static, Input, Button, Select
from textual.containers import Vertical, Horizontal

BATT_STAT_MAP = {"Normal": "Normal", "Low": "Low", "Depleted": "Depleted", "Unknown": "unknown (CHK_BAT)", "Any": "Any"}
BATT_STAT_REVERSE = {v: k for k, v in BATT_STAT_MAP.items()}

class ParametersScreen(ModalScreen):

    CSS_PATH = "../assets/generate_report_screen.css"
    BINDINGS = [
        ("up",    "focus_previous"),
        ("down",  "focus_next"),
        ("left",  "focus_previous"),
        ("right", "focus_next"),
    ]

    def __init__(self, params: dict):
        super().__init__()
        self._params = params

    def compose(self) -> ComposeResult:
        with Vertical(id="params-screen"):
            yield Static("=== Parameters ===", id="params-title")
            with Vertical(id="params-list"):
                with Horizontal(classes="param-row"):
                    yield Static("Below Battery:", classes="param-label")
                    yield Select(
                        [("True", True), ("False", False)],
                        value=self._params["below_batt"],
                        allow_blank=False,
                        id="below-batt-select"
                    )
                with Horizontal(classes="param-row"):
                    yield Static("Battery Threshold:", classes="param-label")
                    yield Input(value=str(self._params["batt_threshold"]), id="batt-threshold-input")
                with Horizontal(classes="param-row"):
                    yield Static("Alarm Present:", classes="param-label")
                    yield Select(
                        [("True", True), ("False", False)],
                        value=self._params["audible_alm"],
                        allow_blank=False,
                        id="audible-alm-select"
                    )
                with Horizontal(classes="param-row"):
                    yield Static("Below Load:", classes="param-label")
                    yield Select(
                        [("True", True), ("False", False)],
                        value=self._params["below_load"],
                        allow_blank=False,
                        id="below-load-select"
                    )
                with Horizontal(classes="param-row"):
                    yield Static("Load Threshold:", classes="param-label")
                    yield Input(value=str(self._params["load_threshold"]), id="load-threshold-input")
                with Horizontal(classes="param-row"):
                    yield Static("Battery Status:", classes="param-label")
                    yield Select(
                        [(s, s) for s in BATT_STAT_MAP.keys()],
                        value=BATT_STAT_REVERSE[self._params["batt_stat"]],
                        allow_blank=False,
                        id="batt-stat-select"
                    )
            with Horizontal(id="params-buttons"):
                yield Button("Cancel", id="cancel-button")
                yield Button("Apply", id="apply-button")

    def on_mount(self) -> None:
        self.call_after_refresh(self._apply_initial_disabled_states)

    def _apply_initial_disabled_states(self) -> None:
        self.query_one("#batt-threshold-input", Input).disabled = not self._params["below_batt"]
        self.query_one("#load-threshold-input", Input).disabled = not self._params["below_load"]

    @on(Select.Changed, "#below-batt-select")
    def on_below_batt_changed(self, event: Select.Changed) -> None:
        self.query_one("#batt-threshold-input", Input).disabled = event.value is not True

    @on(Select.Changed, "#below-load-select")
    def on_below_load_changed(self, event: Select.Changed) -> None:
        self.query_one("#load-threshold-input", Input).disabled = event.value is not True

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    @on(Select.Changed, "#audible-alm-select")
    def on_alarm_changed(self, event: Select.Changed) -> None:
        alarm_on = event.value is True
        for widget_id in ("#below-batt-select", "#below-load-select", "#batt-stat-select"):
            self.query_one(widget_id, Select).disabled = alarm_on
        for widget_id in ("#batt-threshold-input", "#load-threshold-input"):
            self.query_one(widget_id, Input).disabled = alarm_on
        if alarm_on:
            self.query_one("#below-batt-select", Select).value = False
            self.query_one("#below-load-select", Select).value = False

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#apply-button")
    def on_apply(self) -> None:
        self.dismiss({
            "below_batt":     self.query_one("#below-batt-select",    Select).value,
            "batt_threshold": int(self.query_one("#batt-threshold-input", Input).value),
            "audible_alm":    self.query_one("#audible-alm-select",   Select).value,
            "below_load":     self.query_one("#below-load-select",    Select).value,
            "load_threshold": int(self.query_one("#load-threshold-input", Input).value),
            "batt_stat":      BATT_STAT_MAP[self.query_one("#batt-stat-select", Select).value],
        })
