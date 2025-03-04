from common_term import *
from syncprims import comm_queue, sem_UI, queue_cond
from logger import Logger

class PushChangesScreen(ModalScreen):

    CSS_PATH = "./assets/push_changes_screen.css"

    def __init__(self, ip_change, subnet_change, dhcp_change):
        super().__init__()
        self.ip_change = ip_change
        self.subnet_change = subnet_change
        self.dhcp_change = dhcp_change
        Logger.log(f"[PushChgScreen] Parsed values: {self.ip_change}/{self.subnet_change}/{self.dhcp_change}")

    def on_mount(self) -> None:
        self.message = self.query_one("#message", Label) 

    def compose(self) -> ComposeResult:
        
        yield Grid(
            Label("Are you sure you want to submit these changes?", id="message"),
            Container(
                Button("Yes", variant="default", id="yes"),
                Button("No", variant="primary", id="no"),
            classes="buttons"),
            id="dialog",
        )


    # send a request and receive a response
    async def send_request(self, request_type: str, message=None) -> tuple:
        request = {
                                'request': request_type,
                                'message': message
        } 
        Logger.log(f"requesting: req -> {request.get("request")} msg -> {request.get("message")} / sem_UI:{sem_UI}")
        with queue_cond:
            comm_queue.put(request)
            queue_cond.notify() # let listen() know there's a request-- let go of lock too!
                
        sem_UI.acquire()
        response = dict(comm_queue.get()).get("message")
        Logger.log(f"response: {response}")
        return response

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if event.button.id == "yes":

            # remove the buttons
            buttons = self.query_one(".buttons")
            buttons.remove()

            #update the label
            self.message.update("Pushing Changes. Please wait.")
            
            #await changes
            try:
                await self.send_request("SET_IP", message=self.ip_change)
            except Exception as e:
                Logger.log(f"Error pushing change: {str(e)}")


            try:
                self.message.update("Restarting card. Please wait.")
                
                restart_success: bool = await self.send_request("RESTART")
                # notify the UI to update the reactive messages on screen
                # self.post_message(self.RestartMsg(restart_success))
                if restart_success:
                    self.message.update("Restart successful!")
                else:
                    self.message.update("Restart failed. Try again.")

                # Add the buttons container again, this time with only ONE button 
                buttons_container = Container(classes="buttons")
                self.query_one("#dialog", Grid).mount(buttons_container)
                ok_button = Button("OK", id="ok-button", variant="primary")
                buttons_container.mount(ok_button)

            except Exception as e:
                Logger.log(f"Error restarting webcard: {e}")

        elif event.button.id == "no" or event.button.id == "ok":
            self.app.pop_screen()
    

    async def push_changes(self) -> None:
        
        if self.ip_change != "":
            result = await self.send_request("SET_IP", message=self.ip_change)
        # if self.subnet_change is not "":
        #     await send_request("SET_SUBNET", message=self.subnet_change)
        # if self.dhcp_change is not None and self.dhcp_change is True:
        #     await send_request("SET_DHCP")
        # elif self.dhcp_change is not None and self.dhcp_change is False:
        #     await send_request("SET_STATIC")
