from common.common_term import *
from common.common_imports import os
from .QuitScreen import QuitScreen
from .ModNetworkScreen import ModNetworkScreen
from .EditScreen import EditScreen
from logger import Logger
from .BatchScreen import BatchScreen
import asyncio
from syncprims import send_request

# Displayed right after login for user options.
class OptionsScreen(Screen):

    CSS_PATH="../assets/terminal_opts.css"

    BINDINGS = [
        ("q", "quit_app"),
        ("e", "edit_settings"),
        ("1", "mod_network_settings"),
        ("6", "restart_card"),
        ("7", "batch_operations")
    ]

    def __init__(self):
        super().__init__()
        self.path_to_batch: str = ""
        self.path_to_config: str = ""
        self.current_mode: str = "Single (Default)"

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
                Option("", disabled=True),
                "6. Restart Web Card",
                Option("", disabled=True),
                "7. Push Batch Configuration File",
                id="opts-list"
            )       
        
        with Horizontal(id="options-container"):
                yield Button("Q - Quit", id="quit-button")
                yield Button("E - Edit", id="edit-button")
                yield Label(f"Mode: Single (Default)", id="status-label")
                yield Label(f"", id="info-label")
    
    # Quitting the app will ask for confirmation
    def action_quit_app(self) -> None:
        self.app.push_screen(QuitScreen())

    # yield the modify network folder screen
    def action_mod_network_settings(self) -> None:
        self.app.push_screen(ModNetworkScreen())

    # yield the restart card option
    def action_restart_card(self) -> None:
        self.app.push_screen(RestartScreen())
    
    # handle editing settings
    def action_edit_settings(self) -> None:

        #callback function for EditScreen dismissal to reap values
        def check_edit(result: tuple) -> None:    
            mode: str = result[0]
            path_batch: str = result[1]
            path_config: str = result[2]
            # validate with the OS that there is a batch file
            test_batch_path = "\\".join([str(os.path.dirname(os.path.abspath(path_batch))), path_batch])
            if path_batch is None or not os.path.exists(test_batch_path):
                Logger.log(f"Path to batch file does not exist: {test_batch_path}")
                return
                
            # there doesn't have to be a config file. If its already none, then that's fine. (implicit disable)
            test_config_path = "\\".join([str(os.path.dirname(os.path.abspath(path_config))), path_config])
            if not os.path.exists(test_config_path):
                # if config is supplied, but doesn't exist, then disable import mode explicitly.
                Logger.log(f"Path to config file does not exist: {test_config_path}")
                path_config = None # sets to none to indicate the BatchScreen to disable import mode

            # set the global vars
            self.current_mode = mode
            self.path_to_config = path_config
            self.path_to_batch = path_batch

            status_label: Label = self.query_one("#status-label")
            status_label.update(f"Mode: {self.current_mode}")

        self.app.push_screen(EditScreen(), check_edit)
    
    # handle the batch operations
    async def action_batch_operations(self) -> None:
        test = "Batch" in self.current_mode
        Logger.log(f"-> {test} / {self.current_mode} / {self.path_to_batch}")
        Logger.log(f"path to config file: {self.path_to_config}")
        if "Batch" in self.current_mode:
            try:
                creds: tuple = await send_request("REQ_CREDS")
            except Exception as e:
                Logger.log(f"Driver communication error: {e}")
            self.app.push_screen(BatchScreen(self.path_to_batch, self.path_to_config, creds))
        else:
            Logger.log("No batch file loaded onto program.")


# For explicitly requesting to restart ONE device's webcard
class RestartScreen(ModalScreen):
     
    class RestartMsg(Message):
        def __init__(self, success):
            super().__init__()
            self.success = success

    CSS_PATH = "./assets/restart_popup.css"

    async def on_mount(self) -> None:

        self.status_text = self.query_one("#message", Static)
        self.button = self.query_one("#ok", Button)
        self.button.add_class("disabled")
        
        task = asyncio.create_task(self.perform_restart())
        task.add_done_callback(self.handle_task_result)

    # Display layout
    def compose(self) -> ComposeResult:
         yield Grid(
            Static("Restarting in progress. Please wait.", id="message"),
            Button("OK", id="ok", variant="primary", disabled=True),
            id="dialog",
        )
    
    def handle_task_result(self, task):
        # Check for exceptions
        if task.cancelled():
            Logger.log("Perform restart task was cancelled")
        elif task.exception():
            Logger.log(f"Perform restart task failed: {task.exception()}")       
         
    
    # Peform the restart operation by sending a request
    # to the listen() in driver.py
    async def perform_restart(self):

        try:
            Logger.log("Requesting to restart card.")
            restart_success: bool = await send_request("RESTART")
            # notify the UI to update the reactive messages on screen
            # self.post_message(self.RestartMsg(restart_success))
            if restart_success:
                self.status_text.update("Restart successful!")
            else:
                self.status_text.update("Restart failed. Try again.")
                
            self.button.disabled = False
            self.button.remove_class("disabled")
        except Exception as e:
            Logger.log(f"Error restarting webcard: {e}")


    # Handle the only button on-screen, "OK"
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok" and not event.button.disabled:
            self.app.pop_screen()

