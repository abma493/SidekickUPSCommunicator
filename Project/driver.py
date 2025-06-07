from login import setup, login
from syncprims import sem_driver, sem_UI, comm_queue, queue_cond
from common.common_imports import *
from enum import Enum, auto
from logger import Logger
import glob
from restart_card import restart_card
from http_session import http_session
from config_parser import cfg_dat_parser

ENODAT = 0
EDATWR = -1
EIMCFG = -2
SUCCESS = 1

# ENUM for the user requests via UI to driver
class Request(Enum):
    QUIT            = auto()
    RESTART         = auto()
    GET_NTWK_OPS    = auto()
    PUSH_CHANGES    = auto()
    HOLD_CHANGES    = auto()
    GET_DIAGNOSTICS = auto()
    REQ_CREDS       = auto()
    SET_THRESHOLD   = auto()
    

# The Driver class serves as the liason between Textual's UI implementations
# and the classes that specialize playwright's API to communicate in certain ways
# with a Vertiv UPS's webpage.
class Driver(): 

    def __init__(self):
        self.page = None
        self.browser = None
        self.playwright = None
        self.username = ""
        self.password = ""
        self.ip = ""
        self.quit: bool = False
        self.threshold = 90
        self.path_to_batch_file = ""
        self.session_dat: dict[str, list[tuple[str, str]]] = {}
        self.temp_dat: dict[str, list[tuple[str, str]]] = {}

    # Driver will defer connection and login (login.py)
    async def init(self):

        await sem_driver.acquire() # 0
        credentials: dict = comm_queue.get()

        #connect and authenticate (playwright)
        success = await self.establish_connect(credentials)
        if not success:
            return # sem_UI is released in establish_connect if connection fails
        success = await self.authenticate(credentials)  
        if not success:
            return # sem_UI is released in authenticate if login fails
          
        # load the resources to provide configuration options
        await self.load_comms_tab()
        try:
            cfg_file = await http_session(self.ip, self.username, self.password)
        except Exception as e:
            Logger.log(f"General failure on http_session: {e}")
        if cfg_file is not None:
            self.session_dat = cfg_dat_parser(cfg_file)
            
    # Periodically poll every (n) seconds the playwright page object to see if
    # user has been logged out due to inactivity. If so, re-login the user
    async def chk_for_logout(self):

        Logger.log("CHK_LOGOUT started OK.")
        raise_f:bool = False

        while not self.quit:
            try:
                for _ in range(self.threshold):
                    if self.quit:
                        break
                    await asyncio.sleep(1)
                
                Logger.log(f'CHK_LOGOUT triggered by threshold of {self.threshold} seconds')
                try:
                    await self.page.wait_for_url(
                        lambda url: url.startswith(f"http://{self.ip}/web/initialize.htm?mode=sessionTmo"), timeout=1000
                    )
                    Logger.log("LOGOUT Flag raised.")
                    login_success = await login(self.page, self.username, self.password)
                    
                    if login_success:
                        await self.load_comms_tab()
                        Logger.log("Successful re-login after inactivity.")
                    else:
                        raise_f = True
                        Logger.log("Fatal error on auto-login after inactivity logout.")
                except:
                    if raise_f:
                        raise

            except Exception as e:
                Logger.log(f'CHK_LOGOUT error: {e}')

    # Set a connection with an IP, if successful AND a single IP operation request,
    # then connection is maintained. Otherwise (batch operation), single IP from the batch is
    # used (manually) to verify a valid Vertiv account
    async def establish_connect(self, credentials: dict):
        # Setup the browser connection

        Logger.log(f"Attempting to establish a connection with {credentials.get('ip')}")
        web = f'http://{credentials.get("ip")}/web/initialize.htm'
        
        self.page, self.browser, self.playwright = await setup(web)

        if self.page is None or self.browser is None or self.playwright is None:
            response = {
                'message': "Reaching host(s) failed.\nTry another IP or verify the one you entered."
            }
            Logger.log("Session unreachable.\n")
            comm_queue.put(response)
            sem_UI.release()
            return False # failed to connect
        
        return True # connection established successfully

    # Handles the authentication 
    async def authenticate(self, credentials):
        
        Logger.log(f"Credentials -> [username: {credentials.get('username')} password: {credentials.get('password')} IP: {credentials.get('ip')}]")
        
        # Call the async login function
        login_success: bool = await login(self.page, credentials.get("username"), credentials.get("password"))
        
        response = {
            'login': login_success,
            'message': "Login successful." if login_success else "INFO: Login failed due to\n bad credentials. Try again."
        }

        comm_queue.put(response)
        sem_UI.release() # UI retrieves response (becomes 1 for UI to play around with)
        
        if login_success:
            self.username = credentials.get("username")
            self.password = credentials.get("password")
            self.ip = credentials.get("ip")
            return login_success # login successful
        else:
            Logger.log("Login failed.\n")
            return False # login failed

    # listen for requests from the UI thread. (GET/SET)
    # GET : for UI component at load time
    # SET : user requests by UI interaction
    async def listen(self):   
        Logger.log("Driver listener started OK.")
        
        while not self.quit:
            async with queue_cond:

                # use a Condition lock to wait until a request is present
                while comm_queue.empty(): 
                    await queue_cond.wait()

                response: dict = comm_queue.get()       # Retrieve UI request

                # A race condition occurs when the driver's listen() retrieves the
                # response it put in the queue, since it got to the queue before the UI
                if not response.get('is_request', False):
                    Logger.log("Race condition detected: Driver attempted to read its own response.")
                    comm_queue.put(response) # put the response back
                    await queue_cond.wait() # wait for the next notify()
                    continue

                action: str = response.get("request")   # retrieve the request
                message = response.get("message")       # retrieve the contained msg (if applicable)
                
                # driver processes request accordingly
                msg_reply = await self.parse_request(action, message) 
                
                response['message'] = msg_reply # change the message with reply
                response['is_request'] = False # A response is going back to the queue
                
                # Put back response
                comm_queue.put(response)
                
                sem_UI.release() # UI ready to parse response
                Logger.log(f"sem_UI: {sem_UI._value} triggered by {action} [{msg_reply}]")


    # Takes in a request string and converts it to a Request enum, proceeding to match
    # the enum value with a specific web request. Matched case will defer control to a 
    # function to perform the request and return a result if necessary
    async def parse_request(self, req: str, message):
        
        if req.upper() not in Request.__members__:
            Logger.log("Error parsing request")
            return None # Request failed

        request: Request = Request[req.upper()]
        match request:
            case Request.QUIT:
                await self.cleanup()
                return None
            case Request.RESTART:
                return await self.restart_and_login()
            case Request.GET_NTWK_OPS:
                return self.session_dat['Network.IPv4']
            case Request.PUSH_CHANGES:
                return await self.push_changes()
            case Request.HOLD_CHANGES:
                return self.hold_changes(message)
            case Request.GET_DIAGNOSTICS:
                return await self.get_diagnostics(message)
            case Request.REQ_CREDS:
                return self.send_creds()
            case Request.SET_THRESHOLD:
                return self.set_threshold(message)
            case _:
                pass
        return None 

    # if the user "SETs" changes, they are storing them locally 
    # on the app session, and such changes are "held" by
    # the driver until an explicit "Apply" is selected by user.
    def hold_changes(self, changes: dict[str, list[tuple[str, str]]]):

        if changes is None or not isinstance(changes, dict):
            Logger.log(f"Passed arg in hold_changes is type: {type(changes).__name__}")
            return False
  
        for section, tup_l in changes.items():
            if section in self.temp_dat: # append to existing section
                self.temp_dat[section].extend(tup_l)
            else: # create a new section
                self.temp_dat[section] = tup_l.copy()
        self.test_dat(self.temp_dat, "temp_dat")
        return True

    # if the user explicitly asks to Apply a change during an option
    # or main menu, or if the app asks the user to push changes before 
    # quitting, such func will first update session_dat, then write the
    # contents of it to a file, which will then be imported to the UPS
    async def push_changes(self):
        
        if not self.temp_dat:
            Logger.log("PUSH_CHANGES: No changes to push")
            return ENODAT
        
        for section, tup_l in self.temp_dat.items():
            Logger.log(f'PUSH_CHANGES: Adding {section} content')
            if section not in self.session_dat:
                Logger.log("PUSH CHANGES: Failure during internal data structure writing operation.")
                return EDATWR
            updates = dict(tup_l)
            # if key (k) does not exist in updates, take default value (v), that is, the
            # original one in the session_dat dict
            self.session_dat[section] = [
                (k, updates.get(k, v)) for k, v in self.session_dat[section]
            ]
        try:
            # write the session_dat to a file
            with open("config.txt", 'w', encoding='utf-8') as f:
                for section, k_v_pairs in self.session_dat.items():
                    f.write(f'[{section}]\n')
                    for k, v in k_v_pairs:
                        f.write(f"{k}: {v}\n")
                    f.write("\n")
            # call import operation on device, and do a restart
            success = await http_session(self.ip, self.username, self.password, Operation.IMPORT, "config.txt")
            if success:
                self.temp_dat.clear() # clear the temp storage as changes are saved
        except Exception as e:
            Logger.log(f'Error at push_changes: {e}')

        return SUCCESS if success else EIMCFG
        

    # Function to cleanup driver resources
    async def cleanup(self, quit=True):
        Logger.log("CLEANUP on exit.")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        for f in glob.glob("config*.txt"):
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
        if quit:
            self.quit = True
    
    # In the event that the playwright session is abnormally closed,
    # this function will re-establish the session.
    async def re_establish_connection(self):
        await self.cleanup(quit=False) # make sure all is closed before re-establishing connection
        credentials = {'ip': self.ip, 'username': self.username, 'password': self.password}
        await self.establish_connect(credentials)
        await self.authenticate(credentials)
        await self.load_comms_tab()


    # Requests a restart from Playwright API to Vertiv site
    # Upon receiving a successful reboot attempt, it will log back in with
    # app-cached credentials (TODO: cred storage should be made safer)
    async def restart_and_login(self):  

        try:
            if self.page is None or self.page.is_closed() or self.browser is None or not self.browser.is_connected():
                try:
                    await self.re_establish_connection()
                except Exception as e:
                    Logger.log(f"Critical failure on restart: {e}") 
                    return False

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
            Logger.log(f"Failure on restart: {str(e)}")
            return False

    # retrieve the diagnostics file from the device's web server
    async def get_diagnostics(self, ip: str):
        ip = self.ip if ip is None else ip
        try: 
            success = await http_session(ip, self.username, self.password, Operation.DIAGNOSTICS)
        except Exception as e:
            Logger.log(f"GET_DIAGNOSTICS: Failure during operation - {e}")
        
        assert isinstance(success, bool)
        return success

    # set the driver's logout check timer threshold
    def set_threshold(self, time_n):
        if not isinstance(time_n, int):
            return False
        self.threshold = time_n
        return True

    # Load the communications tab resources from the web.
    # This tab is where all operations derive action from.
    async def load_comms_tab(self):
        # Navigate to the communications tab
        try:
            # Switch to default content in Playwright is not needed
            # Find and switch to the tabArea frame
            frame = self.page.frame("tabArea")

            # Find and click the communications tab within the frame
            comms_tab = await frame.wait_for_selector("#tab4", timeout=default_timeout)
            await comms_tab.click()
        except Exception as e:
            Logger.log(f"Error navigating to communications tab: {e}")

    # For debugging purposes only 
    # Will output the contents of a data structure
    # type used internally by the driver for changes made by user for device
    def test_dat(self, dat: dict[str, list[tuple[str, str]]], name: str):

        if dat is None or not isinstance(dat, dict):
            Logger.log(f"Passed arg in hold_changes is type: {type(dat).__name__}")
            return

        Logger.log(f"DEBUG: Outputting internal data structure contents [{name}]")
        for section_name, key_value_pairs in dat.items():
            Logger.log(f"Section: {section_name}")
            for key, value in key_value_pairs:
                Logger.log(f"  {key} = {value}")

    # Get the user credentials from the driver class
    def send_creds(self):
        return (self.username, self.password)