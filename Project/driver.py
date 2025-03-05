import asyncio
from login import setup, login
from ntwk_ops import NetworkOptions
from syncprims import sem_driver, sem_UI, comm_queue, queue_cond
from common.common_imports import *
from enum import Enum, auto
from logger import Logger
from restart_card import restart_card

GRACEFUL_EXIT = 0
ERR_EXIT = -1

class Request(Enum):
    QUIT = auto()
    RESTART = auto()
    GET_NTWK_OPS_R = auto()
    SET_IP = auto()
    SET_SUBNET = auto()
    SET_DHCP = auto()
    SET_STATIC = auto()
    

# The Driver class serves as the liason between Textual's UI implementations
# and the classes that specialize playwright's API to communicate in certain ways
# with a Vertiv UPS's webpage.
class Driver(): 

    def __init__(self):
        self.page = None
        self.browser = None
        self.playwright = None
        self.networkops = NetworkOptions()
        self.username = ""
        self.password = ""
        self.ip = ""

    # Controller will defer connection and login to login.py
    async def init(self):

        sem_driver.acquire()
        credentials: dict = comm_queue.get()
        sem_driver.release()

        # critical part of init: connect and authenticate
        await self.establish_connect(credentials)
        await self.authenticate(credentials)    

        # Fetch the communications tab 
        await asyncio.sleep(mini_wait)
        
        await self.load_comms_tab()

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
            self.networkops.page = self.page

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
                self.username = credentials.get("username")
                self.password = credentials.get("password")
                self.ip = credentials.get("ip")
                break

            Logger.log("Login failed.\n")

        sem_driver.acquire() # should be 1 THEN decrement at successful login


    # listen for requests from the UI thread. (GET/SET)
    # GET : for UI component at load time
    # SET : user requests by UI interaction
    async def listen(self):
        
        while True:
            
            with queue_cond:
                # use a Condition lock to wait until a request is present
                while comm_queue.empty(): 
                    Logger.log("listen() waiting... (lets go of lock)")
                    queue_cond.wait()

                Logger.log(f" (Lock reacquired) Queue has requests to process...")
                response: dict = comm_queue.get() # Retrieve UI request
                action: str = response.get("request")
                message = response.get("message")
                msg_reply = await self.parse_request(action, message)
                
                response['message'] = msg_reply # change the message with reply
                
                # Put back response
                comm_queue.put(response)
                
                sem_UI.release() # UI ready to parse response
                Logger.log(f"sem_UI: {sem_UI._value} triggered by {action} [{msg_reply}]")


    # Takes in a request string and converts it to a Request enum, proceeding to match
    # the enum value with a specific web request.
    async def parse_request(self, req: str, message):
        if req.upper() not in Request.__members__:
            Logger.log("Error parsing request")
            return ERR_EXIT # Request failed
        Logger.log(f"Fetching {req} w/ message {message}...")
        request: Request = Request[req.upper()]
        match request:
            case Request.QUIT:
                await self.cleanup()
                return None
            case Request.RESTART:
                return await self.restart_and_login()
            case Request.GET_NTWK_OPS_R:
                return await self.networkops.load_network_folder()
            case Request.SET_IP:
                Logger.log(f"Setting IP: {message}")
                return await self.networkops.set_IP(message)
            case Request.SET_SUBNET:
                Logger.log(f"Setting subnet: {message}")
                return await self.networkops.set_subnet(message)
            case Request.SET_DHCP:
                return await self.networkops.enable_dhcp()
            case Request.SET_STATIC:
                return await self.networkops.enable_static()
            case _:
                Logger.log("NO request parsed")
                pass
        
        return None  # Default return

    # New method to clean up Playwright resources
    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    
    # Requests a restart from Playwright API to Vertiv site
    # Upon receiving a successful reboot attempt, it will log back in with
    # app-cached credentials (TODO: cred storage should be made safer)
    async def restart_and_login(self):  

        try:
            restart_success = await restart_card(self.page, self.ip)
            if restart_success:
                Logger.log("restart complete. Logging back in.")
                
                # there's no reason why this should fail (unless creds are changed)
                login_success: bool = False
                retry_limit = 3
                retry = 0
                while not login_success and retry < retry_limit:
                    login_success = await login(self.page, self.username, self.password)
                    retry += 1
                if not login_success: # retries limit reached, failed login (account locked?)
                    Logger.log("Login failed. Account may be locked or credentials changed.")
                    return False
                else:
                    await self.load_comms_tab()
                    return True # restart good and login back good!
            else:
                Logger.log("Restart failed.")
                return False
        except Exception as e:
            Logger.log(f"Error during restart: {str(e)}")
            return False

    async def load_comms_tab(self):
        # Navigate to the communications tab
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

    # run batch operations
    async def run_batch():
        pass


