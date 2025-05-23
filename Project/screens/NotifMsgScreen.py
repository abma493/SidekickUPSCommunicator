
import sys
from pathlib import Path    
# Add parent directory to path when running as standalone
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent))
    
try:
    from common.common_term import *
except ImportError:
    # If running from screens directory
    import sys
    sys.path.append('..')
    from common.common_term import *

class InvalidConfigScreen(ModalScreen):
    """Modal screen to display invalid configuration file notification."""
    
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

class TestApp(App):
    """Test application to demonstrate InvalidConfigScreen."""
    
    def on_mount(self) -> None:
        # Set the dark blue background to match the main app
        self.screen.styles.background = "darkblue"
        self.push_screen(InvalidConfigScreen())


if __name__ == "__main__":
    app = TestApp()
    app.run()