from common.common_term import *
from syncprims import send_request
from .QuitScreen import QuitScreen
from .PushChangesScreen import PushChangesScreen
from .NotifMsgScreen import NotifMsgScreen
from logger import Logger

class ModNetworkScreen(ModalScreen):
    
    CSS_PATH="../assets/modntwk_screen.css"
    BINDINGS = [
        ("q", "quit_app"),
        ("b", "back_menu"),
    ]
    
    async def on_mount(self):
        
        self.dhcp_checkbox: Checkbox = self.query_one("#dhcp-checkbox")
        self.current_ip = self.query_one("#current-ip", Static)
        self.current_subnet = self.query_one("#current-subnet", Static)
        self.dhcp_checkbox.disabled = True
        self.dhcp_changed = False #flag to track if dhcp was modded, not the value itself
        self.pending_dhcp_change = self.dhcp_changed #by default

        self.call_after_refresh(self.load_resources)

    def handle_task_result(self, task):
        # Check for exceptions
        if task.cancelled():
            Logger.log("Network data task was cancelled")
        elif task.exception():
            Logger.log(f"Network data task failed: {task.exception()}")

    # Pre-populate current Network settings 
    async def load_resources(self):
        try: 

            ntwk_dat = await send_request("GET_NTWK_OPS")
            ntwk_dict = dict(ntwk_dat)        
            ip = ntwk_dict['Static IP Address']
            subnet = ntwk_dict['Subnet Mask']
            dhcp = "ON" if int(ntwk_dict['IP Address Method']) == 1 else "OFF"
            Logger.log(f"received: [IP: {ip}], [subnet: {subnet}], [dhcp: {dhcp}]")
    
            self.current_ip.update(f"Current IP: {ip}" if ip else "Current IP: ERROR")
            self.current_subnet.update(f"Current subnet: {subnet}" if subnet else "Current subnet: ERROR")
            self.dhcp_checkbox.label = "Set DHCP (Currently: ON)" if dhcp else "Set DHCP (Currently: OFF)"
            self.dhcp_checkbox.disabled = False
            self.dhcp_checkbox.value = dhcp
            
        except Exception as e:
            Logger.log(f"Error fetching network data {e}")


    def compose(self) -> ComposeResult:
        yield Grid(
            Container(
                Label("Basic Network Settings"),
                Checkbox(f"Set DHCP (Currently: LOADING)", id="dhcp-checkbox"), 
                Horizontal(
                    Static("IP address:", id="ip-label"),
                    Input(placeholder="IP address", id="ip-field"),
                id="ip-field-container"),
                Horizontal(
                    Static("Subnet mask:", id="subnet-label"),
                    Input(placeholder="Subnet mask", id="subnet-mask-field"),
                id="subnet-field-container"),
                Horizontal(
                          Button("SET", id="set-button"),
                          Button("Apply Changes", id="apply-button")),
                Vertical(
                        Static(f"Current IP: LOADING", id="current-ip"),
                        Static(f"Current subnet: LOADING", id="current-subnet"),
                id="current-network-settings"),
            id="configurations"),
            ListView(id="devices-update"),
            Horizontal(
                       Button("Q - Quit", id="quit-button"),
                       Button("B - Back", id="back-button"),
                       Label("Mode: Single (Default)", id="status-label"),
                 id="options"),
        id="ntwk-config-grid")

    def action_quit_app(self) -> None:
        self.app.push_screen(QuitScreen())

    def action_back_menu(self) -> None:
        self.app.pop_screen()


    @on(Button.Pressed, "#set-button")
    async def on_set_pressed(self):
        ip_field = self.query_one("#ip-field", Input)
        subnet_mask_field = self.query_one("#subnet-mask-field", Input)

        success: bool = await send_request("HOLD_CHANGES", {
            "Network.IPv4": [
                ("IP Address Method", "1" if self.dhcp_checkbox.value else "0"),
                ("Static IP Address", str(ip_field.value)),
                ("Subnet Mask", str(subnet_mask_field.value))
            ]           
        })

        notif_message = "Select Apply Changes now or at the main menu to push\n      all changes made to this device."
        if not success:
            Logger.log("Failure to update internal data structure [temp_dat] with values" + 
                       f"{ip_field.value}, {subnet_mask_field.value}, {self.dhcp_checkbox.value}")
            notif_message = "Failure setting user values locally. Either you submitted empty values or check log for details."
        self.app.push_screen(NotifMsgScreen(notif_message))
    
    @on(Button.Pressed, "#apply-button")
    async def on_apply_pressed(self):
        self.app.push_screen(PushChangesScreen())

    @on(Checkbox.Changed, "#dhcp-checkbox")
    def handle_dhcp_checkbox(self, event: Checkbox.Changed):
        # save the value here, True for clicked, False for unclicked
        self.dhcp_changed = True 
        self.pending_dhcp_change = event.value

        