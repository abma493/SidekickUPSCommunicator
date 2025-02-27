from playwright.async_api import Page, expect
import asyncio

class IP_Opts:
    # Folder traversal (Config -> Ntwk -> IPv4)
    def __init__(self, page: Page):
        self.page = page

    async def load_network_folder(self):
        # Switch to default content (not needed in Playwright as it handles frames differently)
        
        # First navigate to the navigation frame
        await self.page.frame_locator("iframe[name='navigationFrame']").wait_for()
        navigation_frame = self.page.frame("navigationFrame")
        
        # Click on config folder
        config_folder = await navigation_frame.wait_for_selector("#report164160")
        await config_folder.click()
        
        # Click on network folder
        network_folder = await navigation_frame.wait_for_selector("#report163850")
        await network_folder.click()
        
        # Click on IPv4 folder
        ipv4_folder = await navigation_frame.wait_for_selector("#report164130") 
        await ipv4_folder.click()

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

    async def enable_dhcp(self):
        try:
            detail_frame = self.page.frame("detailArea")
            
            # Playwright's approach to dropdown selection
            select_element = await detail_frame.wait_for_selector("#enum6138")
            await select_element.select_option(value="0")
            
            # Wait for a moment after selection
            await asyncio.sleep(2)
        except Exception as e:
            print(f'DHCP enable operation failed: {e}')

    async def get_dhcp(self):
        # Placeholder for future implementation
        pass

    async def isset_IPv4(self) -> bool:
        detail_frame = self.page.frame("detailArea")
        checkbox = await detail_frame.wait_for_selector("input[type='checkbox'][id='chkbx6137']")
        return await checkbox.is_checked()