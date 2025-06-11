from common.common_term import *
from playwright.async_api import async_playwright, expect, Page
from restart_card import restart_a_card
from common.common_imports import *
from textual.widgets import Select
from syncprims import send_request
from logger import Logger
from login import login
from asyncio import Task
from .QuitScreen import QuitScreen
from http_session import http_session
import asyncio
import copy

class BatchScreen(Screen):
    
    CSS_PATH = "../assets/batchops.css"

    def __init__(self, path_to_batch: str, path_to_config: str, path_to_firmware: str, current_mode, credentials):
        self.jobs = parse_to_list(path_to_batch)                # dynamic list that will have elements removed upon completion
        self.jobs_c = copy.deepcopy(self.jobs)                  # TODO temporary solution to the "abort all" func
        self.jobs_len = len(self.jobs)                          # holds original len of jobs for final stat
        self.path_to_config = path_to_config                    # config file path (verified to exist)
        self.path_to_firmware = path_to_firmware                # firmware file path (verified to exist)
        self.job_tasks: list[Task] = []                         # Used by "abort all" to purge all jobs (Experimental)
        self.current_mode = current_mode                        # Determines if batch firmware updates are for RDU101/UNITY
        self.credentials = credentials                          # Cached user creds passed here for job completion
        self.running = False                                    # used by "abort all"
        self.mode = Operation.EXPORT                            # determines mode (EXPORT by default, IMPORT or FIRMWARE UP)
        self.success_count = 0                                  # num of jobs completed successfully
        self.small_batch_lim = 5                                # used to limit range of active jobs in large batch files
        self.all_opts = [
            ("Export", True),
            ("Import", bool(self.path_to_config)),
            ("Firmware Update", bool(self.path_to_firmware))
        ]
        super().__init__()

    async def on_mount(self):
        chg_t: bool = await send_request("SET_THRESHOLD", 15)
        if not chg_t:
            self.app.panic("APPLICATION PANIC: FATAL ERROR ADJUSTING CHK_LOGOUT THRESHOLD.")
        self.quit_button = self.query_one("#quit-button", Button)
        self.back_button = self.query_one("#back-button", Button)

    def compose(self) -> ComposeResult:
        
        with Grid(id="batch-screen-grid"):
            yield Static("Batch Queue", id="title")
            
            yield ListView(
                *[ListItem(
                    Container(
                        Static(f"Job {i}"),
                        Static(f"IP: {job['ip']}"),  
                        ProgressBar(id=job['id'], total=100, show_eta=False),
                        Static(f"Status: READY", id=f"{job['id']}-stat"),
                    classes="job-container"
                    )
                ) for i, job in enumerate(self.jobs, 1)],
            id="list-of-jobs")
            
            with Horizontal(classes="buttons-container"):
                yield Button("<Abort All>", id="abort-all")
                yield Button("<B - Back>", id="back-button")
                yield Button("<Q - Quit>", id="quit-button")
                yield Button("<Run>", id="run-button")
                yield Select(
                    ((option, option) for option, enabled in self.all_opts if enabled),
                    value="Export",
                    prompt="<Select Operation>",
                    id="mode-select"                    
                )

    @on(Button.Pressed, "#return-button")
    async def on_return_pressed(self) -> None:
        chg_t = await send_request("CHG_THRESHOLD", 120)
        self.app.pop_screen()

    @on(Button.Pressed, "#back-button")
    async def on_back_pressed(self) -> None:
        chg_t = await send_request("CHG_THRESHOLD", 120)
        self.app.pop_screen()
    
    @on(Button.Pressed, "#quit-button")
    def on_quit_pressed(self) -> None:
        self.app.push_screen(QuitScreen())

    @on(Button.Pressed, "#abort-all")
    async def on_abort_pressed(self) -> None:

        if self.running:
            current = asyncio.current_task()
            for i, task in enumerate(self.job_tasks):

                if task != current:
                    job_id = self.jobs_c[i]["id"]
                    self.mark_job_aborted(job_id)
                    task.cancel()
            self.running = False
            self.back_button.disabled = False
            self.quit_button.disabled = False


    @on(Button.Pressed, "#run-button")
    async def on_run_pressed(self) -> None:
        self.back_button.disabled = True # Unable to go "back" to prev screen
        self.quit_button.disabled = True # Unable to quit the app
        self.run_worker(self.run_batch_ops(), exclusive=True)

    @on(Select.Changed, "#mode-select")
    def on_mode_changed(self, event: Select.Changed) -> None:
        
        mode: Operation = Operation.EXPORT if event.value == "Export" else Operation.IMPORT
        mode = Operation.FIRMWARE if event.value == "Firmware Update" else mode

        self.mode = mode

    # ancillary function to handle job labels and progress bar
    def mark_job_aborted(self, job_id: str) -> None:
        stat_label = self.query_one(f"#{job_id}-stat", Static)
        progress_bar: ProgressBar = self.query_one(f"#{job_id}", ProgressBar)
        stat_label.update("ABORTED")
        progress_bar.update(total=100, progress=0)
    
    # amalgamates all the tasks to run concurrently
    async def run_batch_ops(self):

        self.running = True # jobs begin to run from this point onwards

        while self.jobs:

            # fifo retrieval of 5 jobs into a list (l) 
            small_jobs_l = self.jobs[:min(self.small_batch_lim, len(self.jobs))]
            # update the main batch list by removing the items to be processed
            self.jobs = self.jobs[min(self.small_batch_lim, len(self.jobs)):]            

            tasks = [asyncio.create_task(self.run_job(job["ip"], job["id"])) for job in small_jobs_l]
            
            # place them at class scope to be stopped on user request
            self.job_tasks = tasks
            # all jobs run in parallel, asyncio reaps them when completed/terminated
            await asyncio.gather(*tasks)
        
        # jobs are done processing
        self.running = False

        # Pop the buttons off the stack to leave only the return button when all is done
        buttons_container = self.query_one(".buttons-container")
        buttons_container.remove_children()
        return_button = Button("RETURN", id="return-button", variant="primary")
        final_stat = Static(f"jobs succeeded: ({self.success_count}/{self.jobs_len})", id="final-stat")
        buttons_container.mount(return_button)
        buttons_container.mount(final_stat)

    # Run a single job and perform the select operation (EXPORT/IMPORT/FIRMWARE_UPDATE)
    # TODO: This function needs to have subroutines bc its too long.
    async def run_job(self, ip: str, id: str, max_retries: int = 3):
        stat_label = self.query_one(f"#{id}-stat", Static)
        prog_bar = self.query_one(f"#{id}", ProgressBar)
        retry = 0
        
        while retry < max_retries:
            try:
                stat_label.update("Connecting...")
                
                if self.mode == Operation.FIRMWARE:
                    playwright = await async_playwright().start()
                    browser = await playwright.firefox.launch(headless=True)
                    context = await browser.new_context() 
                    url = f"http://{ip}/web/initialize.htm"
                    page = await context.new_page()
                    await page.goto(url)
                    login_success = await login(page, self.credentials[0], self.credentials[1])
                    if login_success:
                        # Navigate to the communications tab
                        prog_bar.advance(30)
                        stat_label.update("Accessing config folder...")
            
                        # Find and click the communications tab within the frame
                        comms_tab = await page.frame("tabArea").wait_for_selector("#tab4", timeout=default_timeout)
                        await comms_tab.click()

                        # go to the nav frame
                        navigation_frame = page.frame("navigationFrame")
                        await page.wait_for_timeout(1000)
                        
                        # access the Support folder
                        support_folder = await navigation_frame.wait_for_selector("#report164190", timeout=10000)
                        await support_folder.click()

                        # Check firmware version selected over the one read from current device (job)
                        devstat_frame = page.frame("deviceStatus")
                        devmodel = await devstat_frame.locator("#devName0").text_content()
                        if "GXT5" in devmodel and "UNITY" in self.current_mode:
                            raise ModeMismatch(f"{devmodel} cannot receive a UNITY firmware update.") 
                        if "GXT4" in devmodel and "RDU101" in self.current_mode:
                            raise ModeMismatch(f"{devmodel} cannot receive an RDU101 firmware update.")

                        # Select the firmware update folder                       
                        firmware_folder = await navigation_frame.wait_for_selector("#report164380", timeout=10000)
                        await firmware_folder.click()
                        
                        # Click the enable button 
                        detail_frame = page.frame("detailArea")
                        enable_button = await detail_frame.wait_for_selector("#enableComms")
                        await enable_button.click() 

                        # Select the web option for firmware update
                        web_button = await detail_frame.wait_for_selector("#webFwUpdateBtn")
                        await web_button.click()
                        
                        # handle firmware update
                        await self.perform_firmware_update(page, stat_label, ip, id)   
                        prog_bar.advance(30) 
                        stat_label.update("DONE")          
                        break           

                else: # Export or import mode

                    if self.mode == Operation.EXPORT:
                        await http_session(ip, self.credentials[0], self.credentials[1], Operation.EXPORT, None, stat_label, prog_bar)
                    elif self.mode == Operation.IMPORT:
                        await http_session(ip, self.credentials[0], self.credentials[1], Operation.IMPORT, self.path_to_config, stat_label, prog_bar)
                        await restart_a_card(ip, self.credentials[0], self.credentials[1]) # Restart the web card after import
                self.success_count+=1
                break 
            except ModeMismatch as e: # Cancel job due to incompatibility
                Logger.log(f"Job #{id} [{ip}] failure : {e.get_err_msg()}")
                prog_bar.update(total=100, progress=0)
                stat_label.update(e.get_err_msg()) 
                break
            except Exception as e:
                retry += 1
                Logger.log(f"Job #{id} [{ip}] failure : {e}")
                prog_bar.update(total=100, progress=0)
                stat_label.update(f"General failure. Retry: {retry}/{max_retries}")  
                await asyncio.sleep(5) # let the message show    
            finally:
                if self.mode == Operation.FIRMWARE:
                    await context.close()   
                    browser.close()
                    await playwright.stop()   

    # Update the firmware on the unit by fetching imported user file
    async def perform_firmware_update(self, page: Page, stat_label, ip, id):

        try:
            # wait for the web url to show
            await page.wait_for_url(
                lambda url: url.startswith(f"http://{ip}/protected/firmware/httpFwUpdate.html"), timeout=30000
            )
            
            # wait for the detail panel and form to render
            page.locator('div[id="DetailPanelAreaFwUpdate"][style*="visibility: visible"]').wait_for(state="visible")
            page.locator('form[name="firmwareHttpForm"]').wait_for(state="visible")

            #  Click the Browse button and prep to select file
            async with page.expect_file_chooser() as fc_info:
                await page.locator('form[name="firmwareHttpForm"] input[id="Firmware File Upload"]').click()
            
            stat_label.update("Uploading file...")
            self.query_one(f"#{id}", ProgressBar).advance(10) 
            
            # upload the file
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.path_to_firmware)       
            
            # submit the firmware
            update_button = await page.wait_for_selector("#Submit")
            await update_button.click()

            # Check the stat element when available
            stat_element = page.locator("#updProgressString2")
            await stat_element.wait_for(state="visible", timeout=50000)

            # writing is ready
            await expect(stat_element).to_contain_text("Writing", timeout=600000, ignore_case=True)
            stat_label.update("Writing...")
            self.query_one(f"#{id}", ProgressBar).advance(15)

            # rebooting is set (card firmware successful) May take up to 10 minutes
            await expect(stat_element).to_contain_text("rebooting", timeout=600000, ignore_case=True)
            stat_label.update("Rebooting card...")
            self.query_one(f"#{id}", ProgressBar).advance(15)

            # click on the return button once its enabled (this is the end of operation)
            await page.locator("#GoHomeB").click(timeout=600000)

        except Exception as e:
            Logger.log(f"An error has occured during firmware update: {e}")
            raise