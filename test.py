from textual.app import App
from textual.widgets import Button, Static
from textual.containers import Container
import asyncio


class ButtonEnableExitDemo(App):
    """Demo app showing a button that enables after 5 seconds and exits when clicked."""

    CSS = """
    Container {
        layout: vertical;
        align: center middle;
        width: 100%;
        height: 100%;
    }
    
    Button {
        margin: 1 0;
    }
    
    #timer {
        height: 1;
        margin-bottom: 1;
    }
    
    #status {
        height: 1;
        margin-bottom: 1;
        color: yellow;
    }
    
    Button.disabled {
        background: gray;
        color: darkgray;
    }
    """

    def compose(self):
        with Container():
            yield Static("Button will be enabled in 5 seconds...", id="timer")
            yield Static("In progress...", id="status")
            yield Button("Exit Application", id="exit_button", disabled=True)

    def on_mount(self):
        """Called when app is mounted."""
        self.button = self.query_one("#exit_button", Button)
        self.timer_text = self.query_one("#timer", Static)
        self.status_text = self.query_one("#status", Static)
        
        # Add a CSS class to show the disabled state visually
        self.button.add_class("disabled")
        
        # Start the countdown task
        asyncio.create_task(self.enable_button_after_delay())

    async def enable_button_after_delay(self):
        """Enable the button after a 5 second delay with countdown."""
        for seconds_left in range(5, 0, -1):
            self.timer_text.update(f"Button will be enabled in {seconds_left} seconds...")
            await asyncio.sleep(1)
            
        self.timer_text.update("Button is now enabled!")
        self.status_text.update("Ready to quit")
        self.status_text.styles.color = "green"
        self.button.disabled = False
        self.button.remove_class("disabled")

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button press event."""
        if event.button.id == "exit_button" and not event.button.disabled:
            self.exit()


if __name__ == "__main__":
    app = ButtonEnableExitDemo()
    app.run()