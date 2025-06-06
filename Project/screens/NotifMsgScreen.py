from common.common_term import * 


class NotifMsgScreen(ModalScreen):
    
    CSS_PATH = "../assets/notifmsg_screen.css"
    
    def __init__(self, message):
        super().__init__()
        self.message = message


    def on_mount(self) -> None:
        self.query_one("#message").update(self.message)

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("", id="message"),
            Button("OK", variant="primary", id="ok"),
            id="dialog",
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.app.pop_screen()
