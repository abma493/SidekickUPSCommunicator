from common.common_term import *
from common.common_imports import os
from .QuitScreen import QuitScreen
from .ModNetworkScreen import ModNetworkScreen
from .HelpScreen import HelpScreen
from .EditScreen import EditScreen
from .NotifMsgScreen import NotifMsgScreen
from .RetrieveDiagScreen import RetrieveDiagnosticsScreen
from .FirmwareScreen import FirmwareScreen
from .RestartScreen import RestartScreen
from logger import Logger
from .BatchScreen import BatchScreen
import asyncio
from syncprims import send_request

# Displayed right after login for user options.
class OptionsScreen(Screen):

    CSS_PATH="../assets/opts_screen.css"

    BINDINGS = [
        ("q", "quit_app"),
        ("e", "edit_settings"),
        ("1", "mod_network_settings"),
        ("2", "get_diagnostics_file"),
        ("3", "push_firmware_update"),
        ("4", "restart_card"),
        ("5", "batch_operations"),
    ]

    def __init__(self):
        super().__init__()
        self.path_to_batch: str = ""
        self.path_to_config: str = ""
        self.path_to_firmware: str = ""
        self.current_mode: str = "Single (Default)"

    def on_mount(self):
        self.screen.styles.background = "darkblue"
        self.screen.styles.border = ("heavy", "white")

    def compose(self) -> ComposeResult:
        yield Static("Sidekick Communicator", id="title") 
        
        with Container(id="list-container"):
            yield OptionList(
                "1. Modify Network Settings",
                Option("", disabled=True),
                "2. Get Diagnostics file(s)",
                Option("", disabled=True),
                "3. Push firmware update",
                Option("", disabled=True),
                "4. Restart Web Card",
                Option("", disabled=True),
                "5. Batch Operations (Import/Export/Firmware)",
                id="opts-list"
            )       
        
        with Horizontal(id="options-container"):
                yield Button("<Q - Quit>", id="quit-button")
                yield Button("<E - Edit>", id="edit-button")
                yield Label(f"Mode: Single (Default)", id="status-label")
                yield Label(f"", id="info-label")
                yield Button("<?>", id="help-button")
    
    # Quitting the app will ask for confirmation
    def action_quit_app(self) -> None:
        self.app.push_screen(QuitScreen())
    
    @on(Button.Pressed, "#quit-button")
    def on_quit_pressed(self) -> None:
        self.app.push_screen(QuitScreen())

    # yield the modify network folder screen
    def action_mod_network_settings(self) -> None:
        self.app.push_screen(ModNetworkScreen())

    # yield the restart card option
    def action_restart_card(self) -> None:
        self.app.push_screen(RestartScreen())

    async def action_get_diagnostics_file(self) -> None:
        batch_mode = True if "Batch" in self.current_mode else False
        self.app.push_screen(RetrieveDiagnosticsScreen(batch_mode, self.path_to_batch))

    async def action_push_firmware_update(self) -> None:
        ip = await send_request("GET_IP")
        if self.path_to_firmware:
            self.app.push_screen(FirmwareScreen(self.path_to_firmware, self.current_mode, ip))
        else:
            self.app.push_screen(NotifMsgScreen("No valid firmware file found."))
    
    @on(Button.Pressed, "#help-button")
    def on_help_pressed(self) -> None:
        self.app.push_screen(HelpScreen())

    # handle editing settings
    def action_edit_settings(self) -> None:
        
        #callback function for EditScreen dismissal to reap values
        async def check_edit(result: tuple) -> None:    
            mode: str = result[0]
            path_batch: str = result[1]
            path_config: str = result[2]
            path_firmware: str = result[3]

            # validate the batch file
            test_batch_path = "\\".join([str(os.path.dirname(os.path.abspath(path_batch))), path_batch])
            if "Batch" in mode and not path_batch or not os.path.exists(test_batch_path):
                path_batch = ""
                # No batch file, revert back to Single Mode
                mode = "Single"            
                # display user error in UI
                self.app.push_screen(NotifMsgScreen(f"Path to batch file does not exist:\n{test_batch_path}"))
                
            # config file is optional. If None or incorrect, "Import" is disabled
            test_config_path = "\\".join([str(os.path.dirname(os.path.abspath(path_config))), path_config])
            if path_config and not os.path.exists(test_config_path):
                path_config = ""
                self.app.push_screen(NotifMsgScreen(f"Path to config file does not exist:\n{test_config_path}"))

            # firmware file is optional. If None or incorrect, "Firmware update" is disabled on both Single/Batch
            test_firmware_path = "\\".join([str(os.path.dirname(os.path.abspath(path_firmware))), path_firmware])
            if path_firmware and not os.path.exists(test_firmware_path):
                path_firmware = ""
                self.app.push_screen(NotifMsgScreen(f"Path to config file does not exist:\n{test_firmware_path}"))

            # set the global vars
            self.current_mode = mode
            self.path_to_config = path_config
            self.path_to_batch = path_batch
            self.path_to_firmware = path_firmware
            # update the UI label
            status_label: Label = self.query_one("#status-label")
            status_label.update(f"Mode: {self.current_mode}") 
            Logger.log(f"All values set. Look at current_mode: {self.current_mode}\npath_to_config {self.path_to_config}") # TEST

        self.app.push_screen(EditScreen(), check_edit)
    
    # handle the batch operations
    async def action_batch_operations(self) -> None:
        if "Batch" in self.current_mode:
            try:
                creds: tuple = await send_request("REQ_CREDS")
            except Exception as e:
                Logger.log(f"Driver communication error: {e}")
            # Pass the validated paths to batch, config, firmware and creds. Bad paths or lack of paths result in 
            # passing None, which BatchScreen handles to disable specific batch operations.
            self.app.push_screen(BatchScreen(self.path_to_batch, self.path_to_config, self.path_to_firmware, self.current_mode, creds))
        else:
            self.app.push_screen(NotifMsgScreen("Please load a valid batch file before accessing this option."))


    # Used by OptionsList UI component to handle selection on "Enter" by user
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        
        index = event.option_index

        option_actions = {
            0: self.action_mod_network_settings,
            2: lambda: self.action_get_diagnostics_file,
            4: lambda: None,
            6: self.action_restart_card,
            8: self.action_batch_operations,
        }

        if index in option_actions:
            action = option_actions[index]
            action()
