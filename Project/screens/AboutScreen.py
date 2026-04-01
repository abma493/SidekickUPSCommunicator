from common.common_term import *

class AboutScreen(ModalScreen):
    """About / version info modal."""

    CSS_PATH = "../assets/about_screen.css"

    def compose(self) -> ComposeResult:
        with Grid(id="about-dialog"):
            yield Static("Sidekick v.3.0", id="about-title")
            yield Static("(c) 2025-2026 Abraham M. Gonzalez", id="about-body")
            yield Button("return", id="about-close-button")

    @on(Button.Pressed, "#about-close-button")
    def on_close_pressed(self) -> None:
        self.app.pop_screen()
