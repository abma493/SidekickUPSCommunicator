from common_term import *
import asyncio
from syncprims import queue_cond, comm_queue, sem_UI
from QuitScreen import QuitScreen
from ntwk_ops import NetworkOptions
from logger import Logger

class NetworkDataResourcesMsg(Message):
    def __init__(self, dhcp, ip, subnet):
        super().__init__()
        self.dhcp = dhcp
        self.ip = ip
        self.subnet = subnet

class ModNetworkScreen(ModalScreen):
    
    CSS_PATH="./assets/modntwk_screen.css"
    BINDINGS = [
        ("q", "quit_app"),
        ("b", "back_menu"),
    ]

    dhcp_stat: reactive = reactive(str, recompose=True)
    current_ip: reactive = reactive(str, recompose=True)
    current_subnet: reactive = reactive(str, recompose=True)
    dhcp_stat_ready: reactive = reactive(False)


    async def _on_mount(self):
        Logger.log("Loading ModNetworkScreen resources...")
        task = asyncio.create_task(self.load_resources())

        task.add_done_callback(self._handle_task_result)

    def _handle_task_result(self, task):
        # Check for exceptions
        if task.cancelled():
            Logger.log("Network data task was cancelled")
        elif task.exception():
            Logger.log(f"Network data task failed: {task.exception()}")


    async def load_resources(self):

        # send a request and receive a response
        async def populate(request_type: str) -> tuple:
            request = {
                                'request': request_type,
                                'message': None
            } 
            with queue_cond:
                comm_queue.put(request)
                queue_cond.notify() # let listen() know there's a request-- let go of lock too!
            
            Logger.log(f"fetching {request_type}")
            
            sem_UI.acquire()
            response = dict(comm_queue.get()).get("message")
            sem_UI.release()
            return response
        
        try: 

            dhcp, ip, subnet = await populate("GET_NTWK_OPS_R")        
            Logger.log(f"received: [IP: {ip}], [subnet: {subnet}], [dhcp: {dhcp}]")
    
            self.post_message(NetworkDataResourcesMsg(dhcp, ip, subnet))
            dhcp_checkbox: Checkbox = self.query_one("dhcp-checkbox")
            dhcp_checkbox.value = True if dhcp == "ON" else False

        except Exception as e:
            Logger.log(f"Error fetching network data {e}")


    def compose(self) -> ComposeResult:
        yield Grid(
            Container(
                Label("IP Modification Options"),
                Checkbox(f"Set DHCP (Currently: {self.dhcp_stat})", id="dhcp-checkbox"), 
                Horizontal(
                    Static("IP address:", id="ip-label"),
                    Input(placeholder="IP address", id="ip-field"),
                id="ip-field-container"),
                Horizontal(
                    Static("Subnet mask:", id="subnet-label"),
                    Input(placeholder="Subnet mask", id="subnet-mask-field"),
                id="subnet-field-container"),
                Vertical(
                        Static(f"Current IP: {self.current_ip}", id="current-ip"),
                        Static(f"Current subnet: {self.current_subnet}", id="current-subnet"),
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

    @on(Checkbox.Changed, "#dhcp-checkbox")
    def handle_dhcp_checkbox(self, event: Checkbox.Changed):
        is_checked = event.value
        if is_checked:
            pass
    
    @on(NetworkDataResourcesMsg)
    def handle_update_labels(self, message: NetworkDataResourcesMsg):

        self.dhcp_stat = "ON" if message.dhcp else "OFF"
        self.current_ip = message.ip if message.ip else "ERROR" 
        self.current_subnet = message.subnet if message.subnet else "ERROR"
        