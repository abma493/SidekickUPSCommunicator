from common_term import *
from syncprims import queue_cond, comm_queue, sem_UI
from QuitScreen import QuitScreen
from ip_opts import IP_Opts

class ModNetworkScreen(ModalScreen):
    
    CSS_PATH="./assets/modntwk_screen.css"
    BINDINGS = [
        ("q", "quit_app"),
        ("b", "back_menu"),
    ]
    dhcp_stat: bool = False
    current_ip: str = ""

    def _on_mount(self):
        IP_Opts.load_network_folder()
        self.pre_populate()

    
    def pre_populate(self):
        
        request_ip = {
                        'request': 'GET_IP',
                        'message': None,
                    }
        
        request_dhcp = {
                        'request': 'GET_DHCP',
                        'message': None
        }

        comm_queue.put(request_ip)
        comm_queue.put(request_dhcp)
        queue_cond.notify()

        # HERE I need to now retrieve the queue from the request
        sem_UI.acquire() # 1 -> 0

        ip = dict(comm_queue.get()).get("message")
        dhcp = dict(comm_queue.get()).get("message")
        self.dhcp_stat = dhcp
        self.current_ip = ip


    def compose(self) -> ComposeResult:
        yield Grid(
            Container(
                Label("IP Modification Options"),
                Checkbox("Set DHCP On", value=self.dhcp_stat, id="dhcp-checkbox"), #needs to update from website
                Horizontal(
                    Static("IP address:", id="ip-label"),
                    Input(placeholder="IP address", id="ip-field"),
                id="ip-field-container"),
                Horizontal(
                    Static("Subnet mask:", id="subnet-label"),
                    Input(placeholder="Subnet mask", id="subnet-mask-field"),
                id="subnet-field-container"),
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

    @on(Checkbox.Changed, "#dhcp-checkbox")
    def handle_dhcp_checkbox(self, event: Checkbox.Changed):
        is_checked = event.value
        if is_checked:
            pass
        