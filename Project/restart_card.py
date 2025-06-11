from playwright.async_api import Page
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from common.common_imports import default_timeout, Logger
from login import login

# restart THIS card, the one that is currently logged in on app initialization
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
        await page.wait_for_url(f"http://{ip}/web/initialize.htm?mode=reboot")
        await page.wait_for_selector("#username", state="visible", timeout=600000)
        return True
    except TimeoutError as e:
        Logger.log(f"Timeout Error during reboot wait: {e}")
        return False
    
# Restart a card by IP address (e.g. for batch mode operations)
async def restart_a_card(ip: str = None, username: str = None, password: str = None) -> bool:
    if ip and username and password:
        playwright = await async_playwright().start()
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context() 
        page = await context.new_page()
        url = f'http://{ip}/web/initialize.htm'
        try:
            await page.goto(url)
            login_success = await login(page, username, password)
            if login_success:
                Logger.log(f"Login successful for {ip}")
                frame = page.frame("tabArea")
                # Find and click the communications tab within the frame
                comms_tab = await frame.wait_for_selector("#tab4", timeout=default_timeout)
                await comms_tab.click()
                Logger.log(f"Attempting to restart card {ip}")
                restart_success = await restart_card(page, ip)
                return restart_success
            else:
                Logger.log(f"Login failed for {ip}.")
                return False
        except PlaywrightTimeoutError as e:
            Logger.log(f"Failed to load page: {e}")
            return False
        except Exception as e:
            Logger.log(f"Failure on page handling : {e}")
            return False
        finally:
            await browser.close()
            await playwright.stop()
    else:
        Logger.log("No IP provided restart.")
        return False