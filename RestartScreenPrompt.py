from common_term import *

class PushChangesScreen(ModalScreen):

    CSS_PATH = "./assets/push_changes_screen.css"

    def compose(self) -> ComposeResult:
        
        yield Grid(
            Label("Are you sure you want to submit these changes?", id="question"),
            Button("Yes", variant="default", id="yes"),
            Button("No", variant="primary", id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if event.button.id == "yes":

            self.query_one("#question", Label).update("Pushing Changes. Please wait.")
            self.query_one("#yes", Button).display = False
            self.query_one("#no", Button).display = False
            self.run_worker(self.push_change(), exclusive=True)

        else:
            self.app.pop_screen()
    
    async def push_change(self) -> None:
        pass