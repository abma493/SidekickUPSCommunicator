from common.common_term import *
from common.manpages import help_pages

class HelpScreen(ModalScreen):
    """Multi-page help modal screen."""
    
    CSS_PATH = "../assets/help_screen.css"
    
    def __init__(self):
        super().__init__()
        self.current_page = 0
    
    def compose(self) -> ComposeResult:
        with Grid(id="help-dialog"):
            yield Label(help_pages[self.current_page]["title"], id="help-title")
            yield Static(help_pages[self.current_page]["content"], id="help-content")
            with Horizontal(id="help-buttons"):
                yield Button("<", id="prev-button", disabled=(self.current_page == 0))
                yield Label(f"Page {self.current_page + 1} of {len(help_pages)}", id="page-indicator")
                yield Button(">", id="next-button", disabled=(self.current_page == len(help_pages) - 1))
                yield Button("Close", id="close-button", variant="primary")
    
    @on(Button.Pressed, "#prev-button")
    def on_prev_pressed(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.update_content()
    
    @on(Button.Pressed, "#next-button")
    def on_next_pressed(self) -> None:
        if self.current_page < len(help_pages) - 1:
            self.current_page += 1
            self.update_content()
    
    @on(Button.Pressed, "#close-button")
    def on_close_pressed(self) -> None:
        self.app.pop_screen()
    
    def update_content(self) -> None:
        """Update the help content and navigation buttons."""
        # Update title and content
        self.query_one("#help-title").update(help_pages[self.current_page]["title"])
        self.query_one("#help-content").update(help_pages[self.current_page]["content"])
        
        # Update page indicator
        self.query_one("#page-indicator").update(f"Page {self.current_page + 1} of {len(help_pages)}")
        
        # Update button states
        self.query_one("#prev-button").disabled = (self.current_page == 0)
        self.query_one("#next-button").disabled = (self.current_page == len(help_pages) - 1)


# Test app for standalone running
class TestApp(App):
    """Test application to demonstrate HelpScreen."""
    
    def on_mount(self) -> None:
        self.screen.styles.background = "darkblue"
        self.push_screen(HelpScreen())


if __name__ == "__main__":
    app = TestApp()
    app.run()