from textual.app import App, ComposeResult
from textual.containers import Center
from textual.widgets import Button, Label
import asyncio

class ConfirmDialog(App):
    CSS = """
    Screen {
        align: center middle;
    }
    
    .container {
        width: 50%;
        height: auto;
        border: solid green;
        padding: 2;
    }
    
    #question {
        text-align: center;
        margin-bottom: 1;
        height: 3;
    }
    
    .buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }
    
    Button {
        margin: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Center(classes="container"):
            yield Label("Do you want to continue?", id="question")
            with Center(classes="buttons"):
                yield Button("Yes", id="yes-button", variant="success")
                yield Button("No", id="no-button", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "yes-button":
            # Remove the buttons
            buttons = self.query_one(".buttons")
            buttons.remove()
            
            # Update the label
            self.query_one("#question").update("Processing...")
            
            # Wait for 5 seconds
            await asyncio.sleep(5)
            
            # Update the container with new content
            container = self.query_one(".container")
            container.remove_children()
            
            # Add new content with DIFFERENT ID
            label = Label("Process complete!", id="complete_message")
            container.mount(label)
            
            buttons_container = Center(classes="buttons")
            container.mount(buttons_container)
            
            exit_button = Button("EXIT", id="exit-button", variant="primary")
            buttons_container.mount(exit_button)
                
        elif button_id == "no-button":
            self.exit(0)  # Exit with code 0
            
        elif button_id == "exit-button":
            self.exit(0)  # Exit with code 0

if __name__ == "__main__":
    app = ConfirmDialog()
    app.run()