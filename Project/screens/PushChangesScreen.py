from common.common_term import *
from syncprims import send_request
from logger import Logger
from textual import work

class MessageMsg(Message):
    
    def __init__(self, message: str):
        super().__init__()
        self.message = message

class PushChangesScreen(ModalScreen):

    CSS_PATH = "../assets/push_changes_screen.css"

    def compose(self) -> ComposeResult:
        
        yield Grid(
            Label("Are you sure you want to apply these changes?", id="message"),
            Horizontal(
                Button("Yes", variant="default", id="yes"),
                Button("No", variant="primary", id="no"),
            classes="buttons"),
            id="dialog"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if event.button.id == "yes":

            # remove the buttons
            buttons = self.query_one(".buttons")
            buttons.remove()
            info_message = self.query_one("#message")
            info_message.update("Applying changes. This may take some time.\n" + " " * 13 + "Please wait.")
            self.call_after_refresh(self.push_changes_and_restart)

        elif event.button.id == "no" or event.button.id == "ok-button":
            self.app.pop_screen()


    async def push_changes_and_restart(self):
        try: 
            # request driver to push the changes
            ret_val = await send_request("PUSH_CHANGES")
            if ret_val < 1:
                if ret_val == 0:
                    self.post_message(MessageMsg("No changes were registered on user fields."))
                if ret_val == -1:
                    self.post_message(MessageMsg("A fatal error has occured. Check logs."))
                if ret_val == -2:
                    self.post_message(MessageMsg("Failure on applying changes to device. Try again or restart the application."))
            
            # apply the changes
            self.post_message(MessageMsg("Restarting card. Please wait."))
            restart_success: bool = await send_request("RESTART")
            
            # notify the UI to update the reactive messages on screen
            if restart_success:
                self.post_message(MessageMsg("   Restart successful.\nChanges have been applied."))
            else:
                self.post_message(MessageMsg("Restart failed. Try again."))

        except Exception as e:
            Logger.log(f"Failure during restart operation: {str(e)}")
        finally:
            self.add_ok_button()

    def add_ok_button(self):
        # Add the buttons container again, this time with only ONE button 
        buttons_container = Horizontal(classes="buttons")
        self.query_one("#dialog", Grid).mount(buttons_container)
        ok_button = Button("OK", id="ok-button", variant="primary")
        buttons_container.mount(ok_button)


    @on(MessageMsg)
    def handle_message_update(self, message: MessageMsg):
        info_message = self.query_one("#message")
        info_message.update(message.message)
