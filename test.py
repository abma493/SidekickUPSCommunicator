from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.containers import Center, Middle
from textual.widgets import Button, Label, ProgressBar
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
            yield Button("Run", id="run-button")
            yield Label("Loading", id="question")
            with Center():
                    yield ProgressBar(total=100, show_eta=False)


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "run-button":
            await self.most_func()

    async def most_func(self):
        # Update the label
        self.query_one("#question").update("Processing...")
        await asyncio.sleep(2) #simulate work
        self.query_one(ProgressBar).advance(25)
        self.query_one("#question").update("Please wait...")
        # Wait for 5 seconds
        await asyncio.sleep(5) #simulate work again
        self.query_one(ProgressBar).advance(50)
        self.query_one("#question").update("Almost done...")
        await self.final_func()



    async def final_func(self):
        await asyncio.sleep(3)
        self.query_one("#question").update("DONE!")
        self.query_one(ProgressBar).advance(25)
            

if __name__ == "__main__":
    app = ConfirmDialog()
    app.run()