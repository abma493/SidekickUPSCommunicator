from common_term import *
import asyncio
from syncprims import queue_cond, comm_queue, sem_UI
from QuitScreen import QuitScreen
from ntwk_ops import NetworkOptions

class ModNetworkScreen(ModalScreen):
    
    CSS_PATH="./assets/modntwk_screen.css"
    BINDINGS = [
        ("q", "quit_app"),
        ("b", "back_menu"),
    ]
    dhcp_stat: bool = False
    current_ip: str = ""
    current_subnet: str = ""

    async def _on_mount(self):
        NetworkOptions.load_network_folder(self)

        response_ready = asyncio.Event()

        async def pre_populate(self):
            
            ip = asyncio.create_task(pre_populate_helper("GET_IP"))

            dhcp = asyncio.create_task(pre_populate_helper("GET_DHCP"))
            
            subnet = asyncio.create_task(pre_populate_helper("GET_SUBNET"))
            
            # signal completion
            response_ready.set()
            return ip, dhcp, subnet
        
        task = asyncio.create_task(pre_populate())

        # await for completion
        await response_ready.wait()
        ip, dhcp, subnet = await task

        self.current_ip = ip
        self.current_subnet = subnet
        self.dhcp_stat: bool = dhcp 

        # send a request and receive a response
        async def pre_populate_helper(self, request_type: str):
            request = {
                                'request': request_type,
                                'message': None
            } 

            comm_queue.put(request)
            with queue_cond:
                queue_cond.notify()
            
            await asyncio.to_thread(sem_UI.acquire) # 1 -> 0
            return dict(comm_queue.get()).get("message")



    def compose(self) -> ComposeResult:
        yield Grid(
            Container(
                Label("IP Modification Options"),
                Checkbox("Set DHCP On", value=self.dhcp_stat, id="dhcp-checkbox"), 
                Horizontal(
                    Static("IP address:", id="ip-label"),
                    Input(placeholder="IP address", id="ip-field"),
                id="ip-field-container"),
                Horizontal(
                    Static("Subnet mask:", id="subnet-label"),
                    Input(placeholder="Subnet mask", id="subnet-mask-field"),
                id="subnet-field-container"),
                Vertical(
                        Static(self.current_ip, id="current-ip"),
                        Static(self.current_subnet, id="current-subnet"),
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
        


class ScreenApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        self.push_screen(ModNetworkScreen())


if __name__ == "__main__":
    app = ScreenApp()
    app.run()