from playwright.async_api import Page, expect
import asyncio
from logger import Logger

class NetworkOptions:
    # Folder traversal (Config -> Ntwk -> IPv4)
    def __init__(self, page: Page=None):
        self.page = page
        self._in_edit_mode = False

    async def load_network_folder(self):
        try:
            if not self.page:
                Logger.log("Error: Page is not set in NetworkOptions")
                return
                
            Logger.log("Looking for navigation frame...")
            
            # Get the frame directly by name
            navigation_frame = self.page.frame("navigationFrame")
            
            if not navigation_frame:
                Logger.log("Navigation frame not found")
                return
            
            # Wait for a bit to ensure the frame is fully loaded
            await self.page.wait_for_timeout(1000)
            
            Logger.log("Looking for config folder...")
            config_folder = await navigation_frame.wait_for_selector("#report164160", timeout=10000)
            Logger.log("Clicking config folder...")
            await config_folder.click()
            await self.page.wait_for_timeout(1000)  # Small delay after click
            
            Logger.log("Looking for network folder...")
            network_folder = await navigation_frame.wait_for_selector("#report163850", timeout=10000)
            Logger.log("Clicking network folder...")
            await network_folder.click()
            await self.page.wait_for_timeout(1000)  # Small delay after click
            
            Logger.log("Looking for IPv4 folder...")
            ipv4_folder = await navigation_frame.wait_for_selector("#report164130", timeout=10000)
            Logger.log("Clicking IPv4 folder...")
            await ipv4_folder.click()
            Logger.log("IPv4 folder navigation complete")
            
        except Exception as e:
            Logger.log(f"Error in load_network_folder: {str(e)}")

        try:
            detail_frame = self.page.frame("detailArea")
            edit_button = await detail_frame.wait_for_selector("#editButton")
            await edit_button.click()
            
            select_element = await detail_frame.wait_for_selector("#enum6138")
            current_value = await select_element.evaluate("el => el.value")
            dhcp_stat = "ON" if current_value == "0" else "OFF"

            ip_field = await detail_frame.wait_for_selector("#str6139")
            current_ip = await ip_field.input_value()

            subnet_field = await detail_frame.wait_for_selector("#str6140")
            current_subnet = await subnet_field.input_value()

            return dhcp_stat, current_ip, current_subnet
        except Exception as e:
            print(f"Error parsing network fields: {str(e)}")
            return None, None, None

    async def set_IP(self, IP):
        # Switch to the detail area frame
        detail_frame = self.page.frame("detailArea")
        
        # Click edit button
        edit_button = await detail_frame.wait_for_selector("#editButton")
        await edit_button.click()
        
        # Check if IPv4 is enabled before setting IP
        if await self.isset_IPv4():
            # Find and fill the IP field
            ip_field = await detail_frame.wait_for_selector("#str6139")
            await ip_field.fill(IP)  # In Playwright, fill() clears and types
            
            # Click submit button
            submit_button = await detail_frame.wait_for_selector("#submitButton")
            await submit_button.click()


    async def get_IP(self):
        # Switch to the detail area frame
        detail_frame = self.page.frame("detailArea")
        detail_frame = await self.ensure_edit_mode(detail_frame)

        # Find the IP field
        ip_field = await detail_frame.wait_for_selector("#str6139")

        # Get the current value from the IP field
        current_ip = await ip_field.input_value()
        Logger.log(f"Got IP from playwright: {current_ip}")
        return current_ip
  

    async def enable_dhcp(self):
        try:
            detail_frame = self.page.frame("detailArea")
            detail_frame = await self.ensure_edit_mode(detail_frame)
            # Playwright's approach to dropdown selection
            select_element = await detail_frame.wait_for_selector("#enum6138")
            await select_element.select_option(value="0")
            
            # Wait for a moment after selection
            await asyncio.sleep(2)
        except Exception as e:
            print(f'DHCP enable operation failed: {e}')

    async def isset_IPv4(self) -> bool:
        detail_frame = self.page.frame("detailArea")
        checkbox = await detail_frame.wait_for_selector("input[type='checkbox'][id='chkbx6137']")
        return await checkbox.is_checked()