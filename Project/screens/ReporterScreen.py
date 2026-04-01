from textual.app import App, ComposeResult, on
from textual.screen import Screen
from textual import work
from textual.widgets import Static, ListView, ListItem, Label, ProgressBar, Button, Input
from textual.containers import Container, Horizontal, Vertical, Center, Vertical
from .GenerateReport import GenerateReport
from .AlarmsScreen import AlarmsScreen
# from syncprims import *
import sys
import os

# Add the project root (parent of 'screens/') to the module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from advancedUtils import *
from syncprims import *
from logger import Logger
# from advancedUtils import *
# from syncprims import send_request
# TODO these imports should change to common imports once this module is mounted onto rest of app

_W = 25  # label column width for value alignment


class ReporterScreen(Screen):

    CSS_PATH = "../assets/reporter_screen.css"
    BINDINGS = [
        ("b", "back_menu"),
        ("up", "focus_previous"),
        ("down", "focus_next"),
        ("left", "focus_previous"),
        ("right", "focus_next"),
    ]

    def __init__(self, ip: str):
        super().__init__()
        self._ip = str(ip).strip()

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_back_menu(self) -> None:
        self.app.pop_screen()

    async def on_mount(self):
        self._alarms        = []
        self.ip_label       = self.query_one("#ip-field", Static)
        self.location       = self.query_one("#location-label", Static)
        self.model          = self.query_one("#model-label", Static)
        self.card_type      = self.query_one("#card-type-label", Static)
        self.battery_stat   = self.query_one("#battstat-label", Static)
        self.battery_charge = self.query_one("#batcharge-label", Static)
        self.time_remaining = self.query_one("#timerem-label", Static)
        self.output_stat    = self.query_one("#outstat-label", Static)
        self.output_load    = self.query_one("#outload-label", Static)
        self.battery_temp   = self.query_one("#battemp-label", Static)
        self.active_alarms  = self.query_one("#activealm-label", Static)
        self.alive_status   = self.query_one("#alive-label", Static)
        self.call_after_refresh(self.load_resources)

    @work(thread=True)
    def load_resources(self):
        ip: str = self._ip
        Logger.log(f"ReporterScreen.load_resources: using IP {ip!r}")
        self.app.call_from_thread(self.ip_label.update, f"{'IP:':<{_W}}{ip}")

        alive = is_reachable(ip)
        alive_str = "Reachable" if alive else "Unreachable"
        self.app.call_from_thread(self.alive_status.update, f"{'Alive status:':<{_W}}{alive_str}")

        try:
            if not alive:
                raise RuntimeError("Device unreachable")
            load_data: dict = asyncio.run(ups_status_summary(ip))
            if load_data is None:
                raise RuntimeError("ups_status_summary returned None")
            alarms = []
            try:
                alarms = asyncio.run(ups_alarms_stat(ip))
                self._alarms = alarms
            except Exception as ae:
                Logger.log(f"ups_alarms_stat error: {ae}", level="ERROR")
                self._alarms = []
                self.app.call_from_thread(self.active_alarms.update, f"{'Active Alarms:':<{_W}}Error")

            # call_from_thread is required for all UI updates from a thread
            self.app.call_from_thread(self.location.update,       f"{'Location:':<{_W}}{load_data['Location']}")
            self.app.call_from_thread(self.model.update,          f"{'Model:':<{_W}}{load_data['Model']}")
            self.app.call_from_thread(self.card_type.update,      f"{'Card Type:':<{_W}}{load_data['Card Type']}")
            self.app.call_from_thread(self.battery_stat.update,   f"{'Battery Status:':<{_W}}{load_data['Battery Status']}")
            self.app.call_from_thread(self.battery_charge.update, f"{'Battery Charge %:':<{_W}}{load_data['Battery Charge %']}")
            self.app.call_from_thread(self.time_remaining.update, f"{'Time Remaining (min):':<{_W}}{load_data['Time Remaining (min)']}")
            self.app.call_from_thread(self.output_stat.update,    f"{'Output Status:':<{_W}}{load_data['Output Status']}")
            self.app.call_from_thread(self.output_load.update,    f"{'Output Load %:':<{_W}}{load_data['Output Load %']}")
            self.app.call_from_thread(self.battery_temp.update,   f"{'Battery Temperature (F):':<{_W}}{load_data['Battery Temperature (F)']}")
            self.app.call_from_thread(self.active_alarms.update,  f"{'Active Alarms:':<{_W}}{len(alarms)}")

        except Exception as e:
            Logger.log(f"ReporterScreen.load_resources EXCEPTION: {type(e).__name__}: {e}", level="ERROR")
            self.app.call_from_thread(self.ip_label.update,       f"{'IP:':<{_W}}Error")
            self.app.call_from_thread(self.location.update,       f"{'Location:':<{_W}}Error")
            self.app.call_from_thread(self.model.update,          f"{'Model:':<{_W}}Error")
            self.app.call_from_thread(self.card_type.update,      f"{'Card Type:':<{_W}}Error")
            self.app.call_from_thread(self.battery_stat.update,   f"{'Battery Status:':<{_W}}Error")
            self.app.call_from_thread(self.battery_charge.update, f"{'Battery Charge %:':<{_W}}Error")
            self.app.call_from_thread(self.time_remaining.update, f"{'Time Remaining (min):':<{_W}}Error")
            self.app.call_from_thread(self.output_stat.update,    f"{'Output Status:':<{_W}}Error")
            self.app.call_from_thread(self.output_load.update,    f"{'Output Load %:':<{_W}}Error")
            self.app.call_from_thread(self.battery_temp.update,   f"{'Battery Temperature (F):':<{_W}}Error")
            self.app.call_from_thread(self.active_alarms.update,  f"{'Active Alarms:':<{_W}}Error")
            # alive_status intentionally not overwritten — ping result stays

    def compose(self) -> ComposeResult:
        yield Static("Sidekick Reporter", id="title")
        with Container(id="main-container"):
                yield Vertical(
                    Static("=== UPS Statistics ===", id="subtitle"),
                    Static("LOADING", id="ip-field"),
                    Static("Location: LOADING", id="location-label"),
                    Static("Model: LOADING", id="model-label"),
                    Static("Card Type: LOADING", id="card-type-label"),
                    Static("Battery Status: LOADING", id="battstat-label"),
                    Static("Battery Charge %: LOADING", id="batcharge-label"),
                    Static("Time Remaining (min): LOADING", id="timerem-label"),
                    Static("Output Status: LOADING", id="outstat-label"),
                    Static("Output Load %: LOADING", id="outload-label"),
                    Static("Battery Temperature (F): LOADING", id="battemp-label"),
                    Static("Active Alarms: LOADING", id="activealm-label"),
                    Static("Alive status: LOADING", id="alive-label"),
                id="ups-stat-container")
        with Horizontal(id="query-ups-container"):
                yield Static("Query Device(s): ", id='query-ups-label')
                yield Input(placeholder="Enter an IP", id="ups-query-field")
                yield Button("Search", id="search-button")

        with Horizontal(id="options-container"):
                yield Button("<b - back>", id="back-button")
                yield Button("Generate Report", id="report-button")
                yield Button("See Alarms", id="alarms-button")

    @on(Button.Pressed, "#back-button")
    def on_back_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#report-button")
    def on_generate_report_pressed(self) -> None:
        self.app.push_screen(GenerateReport())

    @on(Button.Pressed, "#alarms-button")
    def on_alarms_pressed(self) -> None:
        self.app.push_screen(AlarmsScreen(self._alarms))

    @on(Button.Pressed, "#search-button")
    async def on_search_pressed(self):
        ip_field = self.query_one("#ups-query-field", Input)
        if not ip_field.value:
             pass # handle "provide IP" message
        else:
             self.loading_ui_message()
             self.get_ups_data(ip_field.value)

    @work(thread=True)
    def get_ups_data(self, ip: str):
        self.app.call_from_thread(self.ip_label.update, f"{'IP:':<{_W}}{ip}")

        alive = is_reachable(ip)
        alive_str = "Reachable" if alive else "Unreachable"
        self.app.call_from_thread(self.alive_status.update, f"{'Alive status:':<{_W}}{alive_str}")

        try:
            if not alive:
                raise RuntimeError("Device unreachable")
            ups_stat: dict = asyncio.run(ups_status_summary(ip))
            if ups_stat is None:
                raise RuntimeError("ups_status_summary returned None")
            alarms = []
            try:
                alarms = asyncio.run(ups_alarms_stat(ip))
                self._alarms = alarms
            except Exception as ae:
                Logger.log(f"ups_alarms_stat error: {ae}", level="ERROR")
                self._alarms = []
                self.app.call_from_thread(self.active_alarms.update, f"{'Active Alarms:':<{_W}}Error")

            self.app.call_from_thread(self.location.update, f"{'Location:':<{_W}}{ups_stat['Location']}")
            self.load_ui_data(ups_stat, alarms)
        except Exception as e:
            Logger.log(f"ReporterScreen.get_ups_data EXCEPTION: {type(e).__name__}: {e}", level="ERROR")
            self.app.call_from_thread(self.ip_label.update,       f"{'IP:':<{_W}}Error")
            self.app.call_from_thread(self.location.update,       f"{'Location:':<{_W}}Error")
            self.app.call_from_thread(self.model.update,          f"{'Model:':<{_W}}Error")
            self.app.call_from_thread(self.card_type.update,      f"{'Card Type:':<{_W}}Error")
            self.app.call_from_thread(self.battery_stat.update,   f"{'Battery Status:':<{_W}}Error")
            self.app.call_from_thread(self.battery_charge.update, f"{'Battery Charge %:':<{_W}}Error")
            self.app.call_from_thread(self.time_remaining.update, f"{'Time Remaining (min):':<{_W}}Error")
            self.app.call_from_thread(self.output_stat.update,    f"{'Output Status:':<{_W}}Error")
            self.app.call_from_thread(self.output_load.update,    f"{'Output Load %:':<{_W}}Error")
            self.app.call_from_thread(self.battery_temp.update,   f"{'Battery Temperature (F):':<{_W}}Error")
            self.app.call_from_thread(self.active_alarms.update,  f"{'Active Alarms:':<{_W}}Error")

    def load_ui_data(self, load_data: dict, alarms: list):
            self.app.call_from_thread(self.model.update,          f"{'Model:':<{_W}}{load_data['Model']}")
            self.app.call_from_thread(self.card_type.update,      f"{'Card Type:':<{_W}}{load_data['Card Type']}")
            self.app.call_from_thread(self.battery_stat.update,   f"{'Battery Status:':<{_W}}{load_data['Battery Status']}")
            self.app.call_from_thread(self.battery_charge.update, f"{'Battery Charge %:':<{_W}}{load_data['Battery Charge %']}")
            self.app.call_from_thread(self.time_remaining.update, f"{'Time Remaining (min):':<{_W}}{load_data['Time Remaining (min)']}")
            self.app.call_from_thread(self.output_stat.update,    f"{'Output Status:':<{_W}}{load_data['Output Status']}")
            self.app.call_from_thread(self.output_load.update,    f"{'Output Load %:':<{_W}}{load_data['Output Load %']}")
            self.app.call_from_thread(self.battery_temp.update,   f"{'Battery Temperature (F):':<{_W}}{load_data['Battery Temperature (F)']}")
            self.app.call_from_thread(self.active_alarms.update,  f"{'Active Alarms:':<{_W}}{len(alarms)}")

    def loading_ui_message(self):
            self.location.update(      f"{'Location:':<{_W}}LOADING")
            self.model.update(         f"{'Model:':<{_W}}LOADING")
            self.card_type.update(     f"{'Card Type:':<{_W}}LOADING")
            self.battery_stat.update(  f"{'Battery Status:':<{_W}}LOADING")
            self.battery_charge.update(f"{'Battery Charge %:':<{_W}}LOADING")
            self.time_remaining.update(f"{'Time Remaining (min):':<{_W}}LOADING")
            self.output_stat.update(   f"{'Output Status:':<{_W}}LOADING")
            self.output_load.update(   f"{'Output Load %:':<{_W}}LOADING")
            self.battery_temp.update(  f"{'Battery Temperature (F):':<{_W}}LOADING")
            self.active_alarms.update( f"{'Active Alarms:':<{_W}}LOADING")
            self.alive_status.update(  f"{'Alive status:':<{_W}}LOADING")
