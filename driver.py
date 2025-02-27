import asyncio
from login import setup, login
from syncprims import sem_driver, sem_UI, comm_queue, queue_cond
from common_imports import *
from enum import Enum, auto
from logger import Logger

GRACEFUL_EXIT = 0
ERR_EXIT = -1

class Request(Enum):
    QUIT = auto()
    GET_IP = auto()
    SET_IP = auto()
    GET_DHCP = auto()
    SET_DHCP = auto()


class Driver(): 
    def __init__(self):
        self.page = None
        self.browser = None
        self.playwright = None

    # Controller will defer connection and login to login.py
    async def init(self):

        sem_driver.acquire()
        credentials: dict = comm_queue.get()
        sem_driver.release()

        await self.establish_connect(credentials)
        await self.authenticate(credentials)    

        # Fetch the communications tab 
        await asyncio.sleep(mini_wait)
        
        # Navigate to the communications tab
        # Note: Playwright doesn't use frames the same way as Selenium
        # This is an approximate conversion that will need testing
        try:
            # Switch to default content in Playwright is not needed
            # Find and switch to the tabArea frame
            frame = self.page.frame("tabArea")
            if frame:
                # Find and click the communications tab within the frame
                comms_tab = await frame.wait_for_selector("#tab4", timeout=default_timeout)
                await comms_tab.click()
            else:
                # If the frame can't be found, try to find it by other means
                frames = self.page.frames
                for frame in frames:
                    if "tabArea" in frame.name:
                        comms_tab = await frame.wait_for_selector("#tab4", timeout=default_timeout)
                        await comms_tab.click()
                        break
        except Exception as e:
            Logger.log(f"Error navigating to communications tab: {e}")

    # Set a connection with an IP, if successful AND a single IP operation request,
    # then connection is maintained. Otherwise (batch operation), single IP from the batch is
    # used (manually) to verify a valid Vertiv account
    async def establish_connect(self, credentials: dict):
        # Setup the browser connection
        
        while True: # VERIFY CONNECTION ESTABLISHED
            
            sem_driver.acquire() # 1 -> 0
            if not comm_queue.empty(): # It must be a retry
                credentials: dict = comm_queue.get()

            Logger.log(f"Attempting to establish a connection with {credentials.get('ip')}")
            web = f'http://{credentials.get("ip")}/web/initialize.htm'
            
            self.page, self.browser, self.playwright = await setup(web)

            if self.page is not None and self.browser is not None and self.playwright is not None:
                break
            
            response = {
                'message': "Reaching host(s) failed.\nTry another IP or verify the one you entered."
            }
            Logger.log("Session unreachable.\n")
            comm_queue.put(response)
            sem_UI.release()
            # sem_driver is 0 so it will wait

        sem_driver.release()
        # Wait a moment before proceeding
        await asyncio.sleep(mini_wait)

    # Handles the authentication 
    async def authenticate(self, credentials):
        while True: # VERIFY LOGIN SUCCESS
            sem_driver.acquire() # 1->0

            if not comm_queue.empty(): # then it must be a retry
                credentials: dict = comm_queue.get()

            Logger.log(f"Credentials -> [username: {credentials.get('username')} password: {credentials.get('password')} IP: {credentials.get('ip')}]")
            
            # Call the async login function
            login_success: bool = await login(self.page, credentials.get("username"), credentials.get("password"))
            
            response = {
                'login': login_success,
                'message': "Login successful." if login_success else "Login failed due to bad credentials. Try again."
            }

            comm_queue.put(response)
            sem_UI.release() # UI retrieves response (becomes 1 for UI to play around with)
            
            if login_success:
                break

            Logger.log("Login failed.\n")

        sem_driver.acquire() # should be 1 THEN decrement at successful login

    async def listen(self):
        while True:
            with queue_cond:
                while comm_queue.empty():
                    queue_cond.wait()

                get_flag: bool = False

                while not comm_queue.empty(): # Could be more than 1 request at once
                    response: dict = comm_queue.get() # Retrieve UI request
                    action: str = response.get("request")
                    get_flag = True if response.get("message") is None else False
                    ret_flag = await self.parse_request(action)
                    if ret_flag == GRACEFUL_EXIT:
                        # Clean up Playwright resources before exiting
                        await self.cleanup()
                        break
                    
                    # Put back response
                    comm_queue.put(response)
                    
                    if get_flag: # The batch requests were for UI
                        sem_UI.release() # UI ready to parse info

    async def parse_request(self, req: str) -> int:
        if req.upper() not in Request.__members__:
            return ERR_EXIT # Request failed
        
        request: Request = Request[req.upper()]
        match request:
            case Request.QUIT:
                return GRACEFUL_EXIT
            case Request.GET_IP:
                # Implement Playwright-specific code for getting IP
                pass
            case Request.GET_DHCP:
                # Implement Playwright-specific code for getting DHCP
                pass
            case _:
                pass
        
        return 0  # Default return

    # New method to clean up Playwright resources
    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()



