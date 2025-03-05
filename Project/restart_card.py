from playwright.async_api import Page
import asyncio
from logger import Logger


async def restart_card(page: Page, ip) -> True:

    navigation_frame = page.frame("navigationFrame")

    await page.wait_for_timeout(1000)

    # Click the support folder
    support_folder = await navigation_frame.wait_for_selector("#report164190", timeout=10000)
    await support_folder.click()

    # Click the enable button 
    detail_frame = page.frame("detailArea")
    enable_button = await detail_frame.wait_for_selector("#enableComms")
    await enable_button.click()
   
    # restart the card
    restart_card_button = await detail_frame.wait_for_selector("#commBtn139")
    
    # click OK on popup 
    page.on("dialog", lambda dialog: dialog.accept())
    await restart_card_button.click()
    Logger.log("Restart occuring...")
    try: # wait for the login prompt to appear again for 10 minutes MAX
        await page.wait_for_url(f"http://{ip}/web/initialize.htm?mode=reboot", timeout=600000)
        return True
    except TimeoutError as e:
        Logger.log(f"Timeout Error during reboot wait: {e}")
        return False