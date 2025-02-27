from common_term import *
from QuitScreen import QuitScreen
from ModNetworkScreen import ModNetworkScreen
from syncprims import queue_cond


class OptionsScreen(Screen):

    CSS_PATH="./assets/terminal_opts.css"

    BINDINGS = [
        ("q", "quit_app"),
        ("e", "edit_settings"),
        ("1", "mod_network_settings")
    ]

    def on_mount(self):
        self.screen.styles.background = "darkblue"
        self.screen.styles.border = ("heavy", "white")

    def compose(self) -> ComposeResult:
        yield Static("Vertiv Configuration Tool", id="title") 
        
        with Container(id="list-container"):
            yield OptionList(
                "1. Modify IP",
                Option("", disabled=True),
                "2. Get Diagnostics file",
                Option("", disabled=True),
                "3 - Update NTP settings",
                Option("", disabled=True),
                "4. Update SMTP Relay settings",
                Option("", disabled=True),
                "5. Push firmware update",
                id="opts-list"
            )       
        
        with Horizontal(id="options-container"):
                yield Button("Q - Quit", id="quit-button")
                yield Button("E - Edit", id="edit-button")
                yield Label("Mode: Single (Default)", id="status-label")
    
    def action_quit_app(self) -> None:
        self.app.push_screen(QuitScreen())

    def action_mod_network_settings(self) -> None:
        self.app.push_screen(ModNetworkScreen())