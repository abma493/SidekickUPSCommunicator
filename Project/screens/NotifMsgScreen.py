from common.common_term import * 


class NotifMsgScreen(ModalScreen):
    
    CSS_PATH = "../assets/notifmsg_screen.css"
    
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Invalid Configuration file selected.", id="message"),
            Button("OK", variant="primary", id="ok"),
            id="dialog",
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.app.pop_screen()
