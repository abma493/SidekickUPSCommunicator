from common.common_term import *
from common.common_imports import *
from playwright.async_api import async_playwright, expect, Page
from login import login
from syncprims import send_request

class FirmwareScreen(ModalScreen):

    CSS_PATH = "../assets/firmware_screen.css"

    def __init__(self, path_to_firmware: str, current_mode: str, ip: str):
        super(FirmwareScreen, self).__init__()
        self.path_to_firmware = path_to_firmware
        self.ip = ip
        self.current_mode = current_mode

    def on_mount(self):
        self.info_msg: Label = self.query_one("#message")
        self.update_button = self.query_one("#update-button")
        self.update_button.disabled = True if not self.path_to_firmware else False

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Perform Firmware Upgrade", id="message"),
            Container(
                Button("Update Now", id="update-button"),
                Button("Return to main screen", id="return-button"),
            classes="buttons"),
        id="prompt")

    @on(Button.Pressed, "#update-button")
    async def on_push_firmware(self):
        self.info_msg.update("Pushing firmware. Please wait.")
        buttons = self.query_one(".buttons")
        buttons.remove()
        self.call_after_refresh(self.push_firmware_upgrade)

    async def push_firmware_upgrade(self):
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.firefox.launch(headless=True)
            context = await browser.new_context() 
            url = f"http://{self.ip}/web/initialize.htm"
            page = await context.new_page()
            await page.goto(url)
            credentials = await send_request("REQ_CREDS")
            login_success = await login(page, credentials[0], credentials[1]) 
            if login_success:
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
                # TODO THIS CHECK NEVER WORKS BECAUSE IT RELIES ON "SINGLE" string
                if "GXT5" in devmodel and "UNITY" in self.current_mode:
                    self.info_msg.update(f"{devmodel} cannot receive a UNITY firmware update.") 
                    raise ModeMismatch(f"{devmodel} cannot receive a UNITY firmware update.") 
                if "GXT4" in devmodel and "RDU101" in self.current_mode:
                    self.info_msg.update(f"{devmodel} cannot receive a RDU101 firmware update.")
                    raise ModeMismatch(f"{devmodel} cannot receive a RDU101 firmware update.")

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
                await self.perform_firmware_update(page)     
                self.info_msg.update("Firmware upgrade complete!")   
            else:
               self.info_msg.update("An internal error has occurred.\nPlease reload the application.")
               Logger.log("Firmware update error on primary device: Credentials corrupted or lost on driver.")    
        
        except ModeMismatch as e:
            self.info_msg.update(f'{e.get_err_msg}')
            Logger.log(f"Firmware upgrade failure: {e.get_err_msg()}")
        except Exception as e:
            self.info_msg.update("General failure upgrading device firmware.")
            Logger.log(f"Failure upgrading device firmware:\n{e}")
        finally:
            self.add_ok_button()

    def add_ok_button(self):
        # Add the buttons container again, this time with only ONE button 
        buttons_container = Horizontal(classes="buttons")
        self.query_one("#prompt", Vertical).mount(buttons_container)
        ok_button = Button("OK", id="ok-button", variant="primary")
        buttons_container.mount(ok_button)

    async def perform_firmware_update(self, page):
        try:
            # wait for the web url to show
            await page.wait_for_url(
                lambda url: url.startswith(f"http://{self.ip}/protected/firmware/httpFwUpdate.html"), timeout=30000
            )
            
            # wait for the detail panel and form to render
            page.locator('div[id="DetailPanelAreaFwUpdate"][style*="visibility: visible"]').wait_for(state="visible")
            page.locator('form[name="firmwareHttpForm"]').wait_for(state="visible")

            #  Click the Browse button and prep to select file
            async with page.expect_file_chooser() as fc_info:
                await page.locator('form[name="firmwareHttpForm"] input[id="Firmware File Upload"]').click()
            
            self.info_msg.update("Uploading file...")
            
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
            self.info_msg.update("Writing...")

            # rebooting is set (card firmware successful) May take up to 10 minutes
            await expect(stat_element).to_contain_text("rebooting", timeout=600000, ignore_case=True)
            self.info_msg.update("Rebooting card...")

            # click on the return button once its enabled (this is the end of operation)
            await page.locator("#GoHomeB").click(timeout=600000)

        except Exception as e:
            Logger.log(f"An error has occured during firmware update: {e}")
            raise        

    @on(Button.Pressed, "#ok-button")
    def on_ok_pressed(self):
        self.app.pop_screen()

    @on(Button.Pressed,"#return-button")
    def on_return_pressed(self):
        self.app.pop_screen()