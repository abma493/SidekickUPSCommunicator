from common.common_term import *
from common.common_imports import asyncio, Logger
from syncprims import send_request

# For explicitly requesting to restart one device's webcard
class RestartScreen(ModalScreen):
     
    class RestartMsg(Message):
        def __init__(self, success):
            super().__init__()
            self.success = success

    CSS_PATH = "../assets/restart_popup.css"

    async def on_mount(self) -> None:

        self.status_text = self.query_one("#message", Static)
        self.button = self.query_one("#ok", Button)
        self.button.add_class("disabled")
        
        task = asyncio.create_task(self.perform_restart())

    # Display layout
    def compose(self) -> ComposeResult:
         yield Grid(
            Static("Restarting in progress. Please wait.", id="message"),
            Button("OK", id="ok", variant="primary", disabled=True),
            id="dialog",
        )       
    
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok" and not event.button.disabled:
            self.app.pop_screen()

