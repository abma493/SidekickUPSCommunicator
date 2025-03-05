from common.common_term import *
from common.common_imports import current_mode, path_to_batch, path_to_config
from .QuitScreen import QuitScreen
from .ModNetworkScreen import ModNetworkScreen
from .EditScreen import EditScreen
from logger import Logger
import asyncio
import os
from syncprims import send_request

# Displayed right after login for user options.
class OptionsScreen(Screen):

    CSS_PATH="../assets/terminal_opts.css"

    BINDINGS = [
        ("q", "quit_app"),
        ("e", "edit_settings"),
        ("1", "mod_network_settings"),
        ("6", "restart_card")
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

        def check_edit(result: tuple) -> None:
            
            mode = result[0]
            path_batch = result[1]
            path_config = result[2]
            
            # set the current mode
            global current_mode, path_to_config, path_to_batch # this may be WRONG!
            current_mode = mode

            # validate with the OS that these file paths are correct
            if path_batch is not None and not os.path.exists(path_batch):
                Logger.log(f"Path to batch file does not exist: {path_batch}")
                current_mode = "Single"
                
            if path_config is not None and not os.path.exists(path_config):
                Logger.log(f"Path to batch file does not exist: {path_batch}")
                current_mode = "Single"
            
            status_label: Label = self.query_one("#status-label")
            status_label.update(f"Mode: {current_mode}")
            
            path_to_config = path_config
            path_to_batch = path_batch

        self.app.push_screen(EditScreen(), check_edit)
            




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

