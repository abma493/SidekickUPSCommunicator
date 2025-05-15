from common.common_term import *
from syncprims import send_request
from logger import Logger

class MessageMsg(Message):
    
    def __init__(self, message: str):
        super().__init__()
        self.message = message

class PushChangesScreen(ModalScreen):

    CSS_PATH = "../assets/push_changes_screen.css"


    def __init__(self, ip_change, subnet_change, dhcp_change):
        super().__init__()
        self.ip_change = ip_change
        self.subnet_change = subnet_change
        self.dhcp_change = dhcp_change
        Logger.log(f"[PushChgScreen] Parsed values: {self.ip_change}/{self.subnet_change}/{self.dhcp_change}")

    def compose(self) -> ComposeResult:
        
        yield Grid(
            Label("Are you sure you want to submit these changes?", id="message"),
            Horizontal(
                Button("Yes", variant="default", id="yes"),
                Button("No", variant="primary", id="no"),
            classes="buttons"),
            id="dialog",
        )


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if event.button.id == "yes":

            # remove the buttons
            buttons = self.query_one(".buttons")
            buttons.remove()
            
            #await changes
            try:
                await self.push_changes()
            except Exception as e:
                Logger.log(f"Error pushing changes: {str(e)}")

            try:
                self.post_message(MessageMsg("Restarting card. Please wait."))
                
                restart_success: bool = await send_request("RESTART")
                # notify the UI to update the reactive messages on screen
                if restart_success:
                    self.post_message(MessageMsg("Restart successful!"))
                else:
                    self.post_message(MessageMsg("Restart failed. Try again."))

                # Add the buttons container again, this time with only ONE button 
                buttons_container = Horizontal(classes="buttons")
                self.query_one("#dialog", Grid).mount(buttons_container)
                ok_button = Button("OK", id="ok-button", variant="primary")
                buttons_container.mount(ok_button)

            except Exception as e:
                Logger.log(f"Error restarting webcard: {str(e)}")

        elif event.button.id == "no" or event.button.id == "ok-button":
            self.app.pop_screen()
    

    async def push_changes(self) -> None:
        
        if self.ip_change != "":
            result = await send_request("SET_IP", message=self.ip_change)
        if self.subnet_change != "":
            result = await send_request("SET_SUBNET", message=self.subnet_change)
        if self.dhcp_change is not None and self.dhcp_change is True:
            result = await send_request("SET_DHCP")
        elif self.dhcp_change is not None and self.dhcp_change is False:
            result = await send_request("SET_STATIC")

    @on(MessageMsg)
    def handle_message_update(self, message: MessageMsg):
        info_message = self.query_one("#message")
        info_message.update(message.message)
