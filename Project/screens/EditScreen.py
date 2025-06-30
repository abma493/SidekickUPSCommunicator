from textual import on
from textual.app import ComposeResult, App
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select


class EditScreen(ModalScreen):
    
    CSS_PATH = "../assets/editscreen.css"

    def __init__(self, mode, path_batch, path_config, path_firmware): 
        super().__init__()
        self.batch_mode = True if "Batch" in mode else False
        self.mode_str = mode
        self.path_batch = path_batch if path_batch else "Path to batch file"
        self.path_config = path_config if path_config else "Path to config file"
        self.path_firmware = path_firmware if path_firmware else "Path to firmware file"
    
    def compose(self) -> ComposeResult:
        
        with Container(id="edit-modal"):
            yield Label("Edit Mode", id="title")
            yield Label(f"Current Mode: {self.batch_mode}", id="mode-label")
            yield Select(
                ((option, option) for option in ["Single", "Batch (RDU101)", "Batch (IS-UNITY)"]),
                value="Single" if "Single" in self.mode_str else self.mode_str,
                prompt="<Select Mode>",
                id="mode-select"
            )
            
            yield Input(id="path-batch", placeholder=self.path_batch, disabled=True)
            yield Input(id="path-config", placeholder=self.path_config, disabled=True)
            # Should be available on both modes, optional unless attempting to push firmware
            yield Input(id="path-firmware", placeholder=self.path_firmware, disabled=False)
            
            yield Button("OK", variant="primary", id="ok-button")
        
    
    def on_mount(self) -> None:
        self.query_one("#mode-select").focus()
    
    @on(Select.Changed, "#mode-select")
    def on_mode_changed(self, event: Select.Changed) -> None:
        
        self.batch_mode = "Batch" in event.value
        path_batch = self.query_one("#path-batch")
        path_config = self.query_one("#path-config")
        mode_label = self.query_one("#mode-label")
        
        # Update the label to show the currently selected mode
        mode_label.update(f"Current Mode: {event.value}")
        
        if self.batch_mode:
            path_batch.disabled = False
            path_config.disabled = False
        else:
            path_batch.disabled = True
            path_config.disabled = True
    
    @on(Button.Pressed, "#firmware-button")
    async def on_firmware_pressed(self) -> None:
        button: Button = self.query_one("#firmware-button")
        updated_label: str = ""

        if button.label == "IS-UNITY":
            updated_label = "RDU101"
        else:
            updated_label = "IS-UNITY"
        button.remove()
        new_button = Button(updated_label, id="firmware-button")
        self.query_one("#firmware-container").mount(new_button)

    @on(Button.Pressed, "#ok-button")
    def on_ok_pressed(self) -> None:

        mode = self.query_one("#mode-select").value
        path_batch = self.query_one("#path-batch").value
        path_config = self.query_one("#path-config").value
        path_firmware = self.query_one("#path-firmware").value

        self.dismiss((mode, path_batch, path_config, path_firmware))
