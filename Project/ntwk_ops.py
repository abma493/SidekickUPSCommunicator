from playwright.async_api import Page
import asyncio
from logger import Logger

class NetworkOptions:
    # Folder traversal (Config -> Ntwk -> IPv4)
    def __init__(self, page: Page=None):
        self.page = page

    # Load the network folder and populate IP/subnet/dhcp-enabled attributes
    async def load_network_folder(self):
        try:
            if not self.page:
                Logger.log("Error: Page is not set in NetworkOptions")
                return
            
            # Get the frame directly by name
            navigation_frame = self.page.frame("navigationFrame")
            
            if not navigation_frame:
                Logger.log("Navigation frame not found")
                return
            
            # Wait for a bit to ensure the frame is fully loaded
            await self.page.wait_for_timeout(1000)
            

            config_folder = await navigation_frame.wait_for_selector("#report164160", timeout=10000)

            await config_folder.click()
            await self.page.wait_for_timeout(1000)  # Small delay after click

            network_folder = await navigation_frame.wait_for_selector("#report163850", timeout=10000)

            await network_folder.click()
            await self.page.wait_for_timeout(1000)  
            

            ipv4_folder = await navigation_frame.wait_for_selector("#report164130", timeout=10000)

            await ipv4_folder.click()
            
        except Exception as e:
            Logger.log(f"Error in load_network_folder: {str(e)}")

        try:
            detail_frame = self.page.frame("detailArea")
            edit_button = await detail_frame.wait_for_selector("#editButton")
            await edit_button.click()
            
            select_element = await detail_frame.wait_for_selector("#enum6138")
            current_value = await select_element.evaluate("el => el.value")
            dhcp_stat = "ON" if current_value == "1" else "OFF"

            ip_field = await detail_frame.wait_for_selector("#str6139")
            current_ip = await ip_field.input_value()

            subnet_field = await detail_frame.wait_for_selector("#str6140")
            current_subnet = await subnet_field.input_value()

            return dhcp_stat, current_ip, current_subnet
        except Exception as e:
            print(f"Error parsing network fields: {str(e)}")
            return None, None, None

    # Set the IP to a user-specified IP
    async def set_IP(self, IP):

        try:
            # Switch to the detail area frame
            detail_frame = self.page.frame("detailArea")
            
            # Click edit button
            edit_button = await detail_frame.wait_for_selector("#editButton")
            await edit_button.click()
            
            # Check if IPv4 is enabled before setting anything
            is_set = await self.isset_IPv4()
            if is_set:
                
                ip_field = await detail_frame.wait_for_selector("#str6139")
                await ip_field.fill(IP)  # In Playwright, fill() clears and types
                
                # Click submit button
                submit_button = await detail_frame.wait_for_selector("#submitButton")
                await submit_button.click()
                return True
            return False
        except Exception as e:
            Logger.log(f"Error setting IP: {str(e)}")

    # Set the subnet to a user-specified subnet
    async def set_subnet(self, subnet):
        
        try:
            # Switch to the detail area frame
            detail_frame = self.page.frame("detailArea")
            
            # Click edit button
            edit_button = await detail_frame.wait_for_selector("#editButton")
            await edit_button.click()
            
            is_set = await self.isset_IPv4()
            if is_set:
                
                subnet_field = await detail_frame.wait_for_selector("#str6140")
                await subnet_field.fill(subnet)  # In Playwright, fill() clears and types
                
                # Click submit button
                submit_button = await detail_frame.wait_for_selector("#submitButton")
                await submit_button.click()
                return True  
            return False    
        except Exception as e:
            Logger.log(f"Error setting subnet: {str(e)}")  

    # Enable DHCP on the web card
    async def enable_dhcp(self):
        
        try:
            # Switch to the detail area frame
            detail_frame = self.page.frame("detailArea")
            
            # Click edit button
            edit_button = await detail_frame.wait_for_selector("#editButton")
            await edit_button.click()
            
            is_set = await self.isset_IPv4()
            if is_set:
                # Find and fill the IP field
                select_element = await detail_frame.wait_for_selector("#enum6138")
                await select_element.select_option(value="1")
                # Click submit button
                submit_button = await detail_frame.wait_for_selector("#submitButton")
                await submit_button.click()
                return True
            return False
        except Exception as e:
            Logger.log(f"Error enabling DHCP: {str(e)}")

    # Enable Static IP addressing on the webcard
    async def enable_static(self):
        
        try:
            # Switch to the detail area frame
            detail_frame = self.page.frame("detailArea")
            
            # Click edit button
            edit_button = await detail_frame.wait_for_selector("#editButton")
            await edit_button.click()
            
            is_set = await self.isset_IPv4()
            if is_set:
                # Find and fill the IP field
                select_element = await detail_frame.wait_for_selector("#enum6138")
                await select_element.select_option(value="0")
                # Click submit button
                submit_button = await detail_frame.wait_for_selector("#submitButton")
                await submit_button.click()
                return True
            return False
        except Exception as e:
            Logger.log(f"Error enabling Static: {str(e)}")
        
    # Verify that IPv4 is allowed
    async def isset_IPv4(self) -> bool:
        detail_frame = self.page.frame("detailArea")
        checkbox = await detail_frame.wait_for_selector("input[type='checkbox'][id='chkbx6137']")
        return await checkbox.is_checked()