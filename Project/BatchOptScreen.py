from common.common_term import *
from playwright.async_api import async_playwright, BrowserContext, TimeoutError as PlaywrightTimeoutError
from common.common_imports import default_timeout
from logger import Logger
from login import login
import asyncio
from datetime import datetime
import os
from logger import Logger

class BatchOptScreen(App):
    
    CSS_PATH = "./assets/batchops.css"

    BINDINGS = [('q', 'quit_app')]

    def __init__(self, jobs, credentials):
        self.jobs = jobs
        self.credentials = credentials
        super().__init__()

    def compose(self) -> ComposeResult:
        
        with Grid(id="batch-screen-grid"):
            yield Static("Batch Queue", id="title")
            
            yield ListView(
                *[ListItem(
                    Container(
                        Static(f"Job {i+1}"),
                        Static(f"IP: {job['ip']}"),  
                        ProgressBar(id=job['id'], total=100, show_eta=False),
                        Static(f"Status: {job['status']}", id=f"stat-job{job['id']}"),
                    classes="job-container"
                    )
                ) for i, job in enumerate(self.jobs)],
            id="list-of-jobs")
            
            with Horizontal(classes="buttons-container"):
                yield Button("Abort All", id="abort-all")
                yield Button("Kill Job", id="kill-button")  
                yield Button("Run", id="run-button")
            

    def action_quit_app(self) -> None:  
        self.app.exit()

    @on(Button.Pressed, "#return-button")
    def action_return_pressed(self) -> None:
        self.app.exit()


    @on(Button.Pressed, "#run-button")
    async def on_run_pressed(self) -> None:
        await self.run_batch_ops()
    
    # amalgamates all the tasks to run
    async def run_batch_ops(self):
        tasks = [self.run_job(job["ip"], job["id"], self.credentials) for job in self.jobs]
        await asyncio.gather(*tasks)

        buttons_container = self.query_one(".buttons-container")
        buttons_container.remove_children()
        OK_button = Button("RETURN", id="return-button", variant="primary")
        buttons_container.mount(OK_button)


    # runs an individual job
    async def run_job(self, ip: str, id: str,  credentials: tuple, max_retries: int = 3):
        
        retry: 0
        
        try:
            self.query_one(f"#stat-job{id}", Static).update("Connecting...")
            playwright = await async_playwright().start()
            browser = await playwright.firefox.launch(headless=False)
            context = await browser.new_context() 
            url = f"http://{ip}/web/initialize.htm"
            page = await context.new_page()
            await page.goto(url)
            
            login_success = await login(page, credentials[0], credentials[1])
            if login_success:
                # Navigate to the communications tab
                self.query_one(f"#{id}", ProgressBar).advance(30)
                self.query_one(f"#stat-job{id}", Static).update("Accessing config folder...")
                try:        
                    # Switch to default content in Playwright is not needed
                    # Find and switch to the tabArea frame
                    frame = page.frame("tabArea")
                    if frame:
                        # Find and click the communications tab within the frame
                        comms_tab = await frame.wait_for_selector("#tab4", timeout=default_timeout)
                        await comms_tab.click()
                    else:
                        # If the frame can't be found, try to find it by other means
                        frames = page.frames
                        for frame in frames:
                            if "tabArea" in frame.name:
                                comms_tab = await frame.wait_for_selector("#tab4", timeout=default_timeout)
                                await comms_tab.click()
                                break
                except Exception as e:
                    Logger.log(f"Error navigating to communications tab: {e}") 
                # TODO for now leave it like this. A job is successful merely by accessing the comms tab. 

                # go to the nav frame
                navigation_frame = page.frame("navigationFrame")
                await page.wait_for_timeout(1000)
                
                # access the Support folder
                support_folder = await navigation_frame.wait_for_selector("#report164190", timeout=10000)
                await support_folder.click()

                # access the Configuration Export/Import
                config_folder = await navigation_frame.wait_for_selector("#report164400", timeout=10000)
                await config_folder.click()

                # Click the enable button 
                detail_frame = page.frame("detailArea")
                enable_button = await detail_frame.wait_for_selector("#enableComms")
                await enable_button.click() 

                self.query_one(f"#{id}", ProgressBar).advance(20)
                self.query_one(f"#stat-job{id}", Static).update("Retrieving file...")   

                # download the file by clicking the "Export" button
                async with page.expect_download() as download:
                    export_button = await detail_frame.wait_for_selector("#commBtn244")
                    await export_button.click() 
                
                download_val = await download.value
                self.query_one(f"#stat-job{id}", Static).update(f"Saving to {download_val.suggested_filename}")
                # save the file (by default it downloads on the current working folder)
                await download_val.save_as(download_val.suggested_filename)

                self.query_one(f"#{id}", ProgressBar).advance(50) 
                self.query_one(f"#stat-job{id}", Static).update("DONE")  

        except PlaywrightTimeoutError as e:
            Logger.log(f"Failed to load page {url} : {e}")
        finally: # close the playwright elements before exiting the job
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
        



if __name__ == "__main__":
    
    jobs = [
        {"ip": "10.5.3.20", "id": "uno", "status": "LOADING"},
        {"ip": "10.5.5.200", "id": "dos", "status": "LOADING"}, 
        # {"ip": "10.5.3.200", "id": "tres", "status": "LOADING"},
        # {"ip": "10.5.21.200", "id": "cuatro", "status": "LOADING"}
    ]
    credentials: tuple = ("admin", "UT$Opu$1812")

    app = BatchOptScreen(jobs, credentials)
    app.run()
