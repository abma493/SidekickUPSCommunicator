from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static, ListView, ListItem, Label, ProgressBar, Button
from textual.containers import Container, Horizontal
# TODO these imports should change to common imports once this module is mounted onto rest of app

# TODO UI screen for ScanNet
class ScanNetScreen(Screen):
    
    CSS_PATH = "../assets/scannet_screen.css"

    def _on_mount(self, event):
        pb = self.query_one(ProgressBar)

    def compose(self) -> ComposeResult:
        yield Static("Sidekick ScanNet", id="title")
        with Container(id="scan-container"):
            yield ListView(
                ListItem(Label(f"No data available.")),
                id="scan-list"
            )
            yield ProgressBar(id="scan-progress", total=100, show_eta=False)
            with Horizontal(id="scan-controls"):
                yield Button("Back", id="back-button")
                yield Button("Cancel", id="cancel-button")
                yield Button("Export", id="export-button")
                yield Button("Parameters", id="params-button")
                yield Button("Begin", id="scan-button")

class ScanNetApp(App):
    CSS_PATH = "../assets/scannet_screen.css"
    
    def on_mount(self) -> None:
        self.push_screen(ScanNetScreen())

if __name__ == "__main__":
    app = ScanNetApp()
    app.run()