from common.common_term import *
from syncprims import send_request


class QuitScreen(ModalScreen):

    CSS_PATH = "../assets/quit_screen.css"

    def compose(self) -> ComposeResult:
        
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            await send_request("QUIT")
            self.app.exit()
        else:
            self.app.pop_screen()
