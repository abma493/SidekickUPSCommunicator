from common.common_term import *

class HelpScreen(ModalScreen):
    """Multi-page help modal screen."""
    
    CSS_PATH = "../assets/help_screen.css"
    
    def __init__(self):
        super().__init__()
        self.current_page = 0
        self.help_pages = [
            {
                "title": "Vertiv Communicator for UPS devices v.1.0",
                "content": """This tool allows you to configure and manage Vertiv GXT4/GXT5

Main features:
• Single device configuration
• Batch operations for multiple devices
• Firmware updates
• Network settings modification
• Configuration file import/export

Press '>' to continue or '<' to go back."""
            },
            {
                "title": "(1) Making Network Changes",
                "content": """Select Option 1.

Options available:
• Set static IP address
• Configure subnet mask
• Enable/Disable DHCP
• View current network configuration

Changes require a device restart to take effect."""
            },
            {
                "title": "(6) Restarting the web card",
                "content": """Safely restart the web card of a UPS device.

This option will:
• Save current configuration
• Restart the device web interface
• Automatically re-login after restart
• Restore your session

The process typically takes 2-3 minutes."""
            },
            {
                "title": "7. Push Batch Configuration File",
                "content": """Apply configurations to multiple devices at once.

Batch operations support:
• Export configurations from multiple devices
• Import configuration files to multiple devices
• Firmware updates across device fleet

Set up batch mode by pressing 'E - Edit' and selecting
either 'Batch (RDU101)' or 'Batch (IS-UNITY)' mode."""
            },
            {
                "title": "Editing Operation Modes and files",
                "content": """Configure the application operating mode.

Available modes:
• Single (Default) - Work with one device at a time
• Batch (RDU101) - Batch operations for RDU101 devices
• Batch (IS-UNITY) - Batch operations for IS-UNITY devices

In batch mode, you must specify:
• Path to batch file (list of IP addresses)
• Path to config file (for import operations)
• Path to firmware file (for firmware updates)"""
            }
        ]
    
    def compose(self) -> ComposeResult:
        with Grid(id="help-dialog"):
            yield Label(self.help_pages[self.current_page]["title"], id="help-title")
            yield Static(self.help_pages[self.current_page]["content"], id="help-content")
            with Horizontal(id="help-buttons"):
                yield Button("<", id="prev-button", disabled=(self.current_page == 0))
                yield Label(f"Page {self.current_page + 1} of {len(self.help_pages)}", id="page-indicator")
                yield Button(">", id="next-button", disabled=(self.current_page == len(self.help_pages) - 1))
                yield Button("Close", id="close-button", variant="primary")
    
    @on(Button.Pressed, "#prev-button")
    def on_prev_pressed(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.update_content()
    
    @on(Button.Pressed, "#next-button")
    def on_next_pressed(self) -> None:
        if self.current_page < len(self.help_pages) - 1:
            self.current_page += 1
            self.update_content()
    
    @on(Button.Pressed, "#close-button")
    def on_close_pressed(self) -> None:
        self.app.pop_screen()
    
    def update_content(self) -> None:
        """Update the help content and navigation buttons."""
        # Update title and content
        self.query_one("#help-title").update(self.help_pages[self.current_page]["title"])
        self.query_one("#help-content").update(self.help_pages[self.current_page]["content"])
        
        # Update page indicator
        self.query_one("#page-indicator").update(f"Page {self.current_page + 1} of {len(self.help_pages)}")
        
        # Update button states
        self.query_one("#prev-button").disabled = (self.current_page == 0)
        self.query_one("#next-button").disabled = (self.current_page == len(self.help_pages) - 1)


# Test app for standalone running
class TestApp(App):
    """Test application to demonstrate HelpScreen."""
    
    def on_mount(self) -> None:
        self.screen.styles.background = "darkblue"
        self.push_screen(HelpScreen())


if __name__ == "__main__":
    app = TestApp()
    app.run()