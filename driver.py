from login import setup,login
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

    # Controller will defer connection and login to login.py
    def init(self):

        sem_driver.acquire()
        credentials: dict = comm_queue.get()
        sem_driver.release()

        driver, wait = self.establish_connect(credentials)
        self.authenticate(driver, wait, credentials)    

        #fetch the communications tab 
        sleep(mini_wait)
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it("tabArea"))
        comms_tab = wait.until(lambda x: x.find_element(By.ID, "tab4"))
        driver.execute_script("arguments[0].click()", comms_tab)

    # Set a connection with an IP, if successful AND a single IP operation request,
    # then connection is maintained. Otherwise (batch operation), single IP from the batch is
    # used (manually) to verify a valid Vertiv account
    def establish_connect(self, credentials: dict):
        # setup the webdriver connection
        
        while True: # VERIFY CONNECTION ESTABLISHED
            
            sem_driver.acquire() # 1 -> 0
            if not comm_queue.empty(): # it must be a retry
                credentials: dict = comm_queue.get()

            Logger.log(f"Attempting to establish a connection with {credentials.get("ip")}")
            web = f'http://{credentials.get("ip")}/web/initialize.htm'
            driver, wait = setup(web)

            if driver is not None and wait is not None:
                break
            
            response = {
                            'message': "Reaching host(s) failed.\nTry another IP or verify the one you entered."
                       }
            Logger.log("Session unreachable.\n")
            comm_queue.put(response)
            sem_UI.release()
            # sem_driver is 0 so it will wait

        sem_driver.release()
        # login to site
        sleep(mini_wait)
        return driver, wait

    # Handles the authentication 
    def authenticate(self, driver, wait, credentials):

        while True: # VERIFY LOGIN SUCCESS

            sem_driver.acquire() # 1->0

            if not comm_queue.empty(): # then it must be a retry
                credentials: dict = comm_queue.get()

            Logger.log(f"Credentials -> [username: {credentials.get("username")} password: {credentials.get("password")} IP: {credentials.get("ip")}]\n")
            login_success : bool = login(wait, driver, credentials.get("username"), credentials.get("password"))
            
            response = {
                        'login' : login_success,
                        'message': "Login successful." if login_success else "Login failed due to bad credentials. Try again."
                    }

            comm_queue.put(response)
            sem_UI.release() # UI retrieves response (becomes 1 for UI to play around with)
            
            if login_success:
                break

            Logger.log("Login failed.\n")

        sem_driver.acquire() # should be 1 THEN decrement at successful login


    def listen(self):
        
        while True:

            with queue_cond:
                
                while comm_queue.empty():
                    queue_cond.wait()

                get_flag: bool = False

                while not comm_queue.not_empty(): # could be more than 1 request at once
                    
                    response : dict = comm_queue.get() # retrieve UI request
                    action: str = response.get("request")
                    get_flag = True if response.get("message") is None else False
                    ret_flag = self.parse_request(action)
                    if ret_flag == GRACEFUL_EXIT:
                        break
                    
                    comm_queue.put()
                    
                    if get_flag: # the batch requests were for UI
                        sem_UI.release() # UI ready to parse info
                    

    def parse_request(self, req: str) -> int:

        if req.upper() not in Request.__members__:
            return ERR_EXIT # request failed
        
        request: Request = Request[req]
        match request:
            case Request.QUIT:
                return GRACEFUL_EXIT
            case Request.GET_IP:
                pass
            case Request.GET_DHCP:
                pass

            



