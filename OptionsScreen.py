from common_term import *
from QuitScreen import QuitScreen
from ModNetworkScreen import ModNetworkScreen
from logger import Logger
import asyncio
from syncprims import queue_cond, comm_queue,sem_UI
from restart_card import restart_card


class OptionsScreen(Screen):

    CSS_PATH="./assets/terminal_opts.css"

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

    def action_restart_card(self) -> None:
        self.app.push_screen(RestartScreen())



# For explicitly requesting to restart ONE device's webcard
class RestartScreen(ModalScreen):
     
    class RestartMsg(Message):
        def __init__(self, success):
            super().__init__()
            self.success = success

    CSS_PATH = "./assets/restart_popup.css"
    message: reactive = reactive(str, recompose=True)

    async def on_mount(self) -> None:
        task = asyncio.create_task(self.perform_restart())

        task.add_done_callback(self.handle_task_result)

    # Display layout
    def compose(self) -> ComposeResult:
         yield Grid(
            Label(self.message, id="message"),
            Button("OK", id="ok", disabled=True),
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

        # parses the request into the queue, sends it and parses
        # the response back to the nesting function
        async def request_restart(request_type: str) -> bool:

            request = {
                                'request': request_type,
                                'message': None
            } 

            with queue_cond:
                comm_queue.put(request)
                queue_cond.notify()
                
            Logger.log("Requesting to restart card.")

            sem_UI.acquire()
            response = dict(comm_queue.get()).get("message")
            sem_UI.release()
            return response
        
        try:
            self.message = "Restarting card. Please wait."
            restart_success: bool = await request_restart("RESTART")
            # notify the UI to update the reactive messages on screen
            self.post_message(self.RestartMsg(restart_success))
        except Exception as e:
            Logger.log(f"Error restarting webcard: {e}")


    # Handle the only button on-screen, "OK"
    def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if not event.button.disabled:
            self.app.pop_screen()
    
    @on(RestartMsg)
    def handle_update(self, message: RestartMsg):
        
        if message.success:
            self.message = "Webcard restart success!"
        else:
            self.message = "Webcard restart Failed. Check log."
            
        ok_button: Button = self.query_one("#ok", Button)
        ok_button.disabled = False # enable the button now
        ok_button.variant = "primary"

