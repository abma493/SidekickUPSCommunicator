from common.common_term import *
from common.common_imports import parse_to_list, asyncio
from syncprims import send_request
from logger import Logger

class RetrieveDiagnosticsScreen(ModalScreen):

    CSS_PATH="../assets/rdiag_screen.css"

    def __init__(self, batch_mode: bool, path_to_batch: str):
        super(RetrieveDiagnosticsScreen, self).__init__()
        self.success_count = 0
        self.batch_mode = batch_mode
        self.path_to_batch = path_to_batch

    def on_mount(self):
        self.info_msg: Label = self.query_one("#message")
        self.batch_button: Button = self.query_one("#batch-retrieval-button")
        self.batch_button.disabled = True if not self.batch_mode else False

    def compose(self) -> ComposeResult:

        yield Vertical(
            Label("Diagnostics File Retrieval", id="message"),
            Container(
                Button("Retrieve from this device only", id="single-retrieval-button"),
                Button("Retrieve from batch devices", id="batch-retrieval-button"),
                Button("Return to main screen", id="return-button"),
            classes="buttons"),
            id="prompt"
        )

    @on(Button.Pressed, "#single-retrieval-button")
    async def on_single_retrieval_pressed(self):
        buttons = self.query_one(".buttons")
        buttons.remove()
        self.info_msg.update("Retrieving file, please wait.")
        self.call_after_refresh(self.retrieve_diagnostics)
        
    @on(Button.Pressed, "#batch-retrieval-button")
    async def on_batch_retrieval_pressed(self):
        buttons = self.query_one(".buttons")
        buttons.remove()
        self.info_msg.update("Retrieving files, this may take some time.")
        self.call_after_refresh(self.run_batch_ops)

    async def run_batch_ops(self):
        small_batch_lim = 5
        jobs = parse_to_list(self.path_to_batch)
        total_jobs = len(jobs)
        while jobs:
            small_jobs_l = jobs[:min(small_batch_lim, len(jobs))]
            jobs = jobs[min(small_batch_lim, len(jobs)):]
            tasks = [asyncio.create_task(self.retrieve_diagnostics(job['ip'])) for job in small_jobs_l]

            await asyncio.gather(*tasks)
        
        self.info_msg.update(f"Diagnostic files retrieved {self.success_count}/{total_jobs}")
        self.add_ok_button()
    
        
    async def retrieve_diagnostics(self, ip=None) -> bool:
        
        try:
            if ip is None: # single device, stored already on driver
                success: bool = await send_request("GET_DIAGNOSTICS")
            else: # multiple device 
                success: bool = await send_request("GET_DIAGNOSTICS", ip)
            if not self.batch_mode or not ip: # single report     
                if not success:
                    self.info_msg.update("General failure retrieving diagnostics file. Check log.")
                    self.add_ok_button()
                else:
                    self.info_msg.update("Diagnostics retrieval success.")
                    self.add_ok_button()
            if success:
                self.success_count+=1
        except Exception as e:
            Logger.log(f"Failure retrieving diagnostics file [{ip}]: {e}")

    def add_ok_button(self):
        # Add the buttons container again, this time with only ONE button 
        buttons_container = Horizontal(classes="buttons")
        self.query_one("#prompt", Vertical).mount(buttons_container)
        ok_button = Button("OK", id="ok-button", variant="primary")
        buttons_container.mount(ok_button)

    @on(Button.Pressed, "#ok-button")
    def on_ok_pressed(self):
        self.app.pop_screen()

    @on(Button.Pressed,"#return-button")
    def on_return_pressed(self):
        self.app.pop_screen()