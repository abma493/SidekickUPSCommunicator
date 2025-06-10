from common.common_term import *


class ConfirmationScreen(ModalScreen):

    CSS_PATH = "../assets/confirm_screen.css"

    def __init__(self, message):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:

        yield Grid(
            Label(self.message, id="question"),
            Button("Yes", variant="error", id="yes-button"),
            Button("No", variant="primary", id="no-button"),
            id="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-button":
            self.dismiss(True)
        else:
            self.dismiss(False)