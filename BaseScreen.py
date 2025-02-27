from common_term import *
from OptionsScreen import OptionsScreen
from textual import work
from syncprims import sem_driver, sem_UI, comm_queue
from logger import Logger

# Ancillary class to support thread-safe UI updates 
class LoginMsg(Message):

    def __init__(self, success: bool):
        super().__init__()
        self.success = success


# This is the Login/Connection screen shown while driver queries 
# the web based on a user-provided IP and validates credentials
class BaseScreen(Screen):

    CSS_PATH = "./assets/terminal.css"
    info_msg: reactive = reactive(str, recompose=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self):
        self.screen.styles.background = "darkblue"
        self.screen.styles.border = ("heavy", "white")
    
    def compose(self) -> ComposeResult:
        yield Static("Vertiv Communicator", id="title")
        yield Static("", classes="box")# empty

        with Vertical(id="main"):

            yield Static("Login", classes="subtitle") 

            with Horizontal(classes="username-container"):
                yield Static("Username:", classes="username-label")
                yield Input(placeholder="Enter username", classes="username-field", id="username")

            with Horizontal(classes="username-container", id="pswd-tester"):
                yield Static("Password:", classes="username-label")
                yield Input(placeholder="Enter password", classes="username-field", id="password", password=True)

            with Horizontal(classes="username-container", id="IP-tester"):
                yield Static("IP address:", classes="username-label", id="optional-batch")
                yield Input(placeholder="IP address", classes="username-field", id="IP")
        
        yield Static("", classes="box") # empty

        with Horizontal(id="ipfiles-button"):
            yield Checkbox("[Supply file of IPs]", value=False,id="checkbox-ipfiles")

        with Horizontal(id="ok-button"):
            yield Button("<OK>", id="ok")

        with Horizontal(id="status"):
            yield Label(f'{self.info_msg}', id="info")


    @on(Button.Pressed, "#ok")
    def on_ok_pressed(self):
        self.info_msg = "INFO: Establishing connection..."

        # worker thread will process login
        self.process_login()
        
    @work(exclusive=True, thread=True)
    def process_login(self):
        Logger.log("Attempting login...")
        inputs = {
            'username' : self.query_one("#username", Input).value,
            'password' : self.query_one("#password", Input).value,
            'ip'       : self.query_one("#IP", Input).value
        }
    
        comm_queue.put(inputs) # login will be attempted 
        sem_driver.release() #0->1

        sem_UI.acquire() # 1->0 from driver to retrieve response

        response: dict = comm_queue.get() # get response and evaluate it 

        message = response.get("message")

        if "login" in response:
            if not response.get("login"): # bad credentials
                self.query_one("#username").value = ""
                self.query_one("#password").value = ""
                self.query_one("#IP").value = ""
                self.post_message(LoginMsg(False)) 
            else:
                sem_driver.release() # driver is good to continue (change to Comms. tab)
                Logger.log("Login OK.")
                self.post_message(LoginMsg(True))
        else:   # web error
            self.query_one("#username").value = ""
            self.query_one("#password").value = ""
            self.query_one("#IP").value = ""
            self.post_message(LoginMsg(False))
        
        Logger.log(f'message parsed: {message}')
        
    
    @on(LoginMsg)
    def handle_login_result(self, message : LoginMsg):
        if message.success:
            self.app.push_screen(OptionsScreen())
            self.info_msg = message


    # TO BE REMOVED 
    def on_check_batch(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "#checkbox-ipfiles":
            if event.value:
                batch_label = self.query_one("#optional-batch", Static)
                batch_label.update("Path to batch file:")
      