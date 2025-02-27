from common_term import *
from OptionsScreen import OptionsScreen
from textual.message import Message
from textual import work
from syncprims import sem_driver, sem_UI, comm_queue
from logger import Logger
import asyncio

# Ancillary class to support thread-safe UI updates 
class LoginMsg(Message):
    def __init__(self, success: bool, message: str = ""):
        super().__init__()
        self.success = success
        self.message = message

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
            yield Checkbox("[Supply file of IPs]", value=False, id="checkbox-ipfiles")

        with Horizontal(id="ok-button"):
            yield Button("<OK>", id="ok")

        with Horizontal(id="status"):
            yield Label(f'{self.info_msg}', id="info")

    @on(Button.Pressed, "#ok")
    async def on_ok_pressed(self):
        self.info_msg = "INFO: Establishing connection..."
        
        # Use the asyncio-compatible login processing
        self.process_login_async()
    
    # Using Textual's work decorator with coroutine=True to run as an async worker
    @work(exclusive=True)
    async def process_login_async(self):
        """Process login using asyncio instead of threads"""
        Logger.log("Attempting login...")
        
        inputs = {
            'username': self.query_one("#username", Input).value,
            'password': self.query_one("#password", Input).value,
            'ip': self.query_one("#IP", Input).value
        }
        
        # Create a future to track when driver is done
        response_ready = asyncio.Event()
        
        # Function to run in a separate thread to handle semaphores
        async def handle_login_flow() -> dict:
            # Put login data in queue
            comm_queue.put(inputs)
            
            # Signal driver to process login
            sem_driver.release()
            # Wait for driver to complete login 
            # (prevent blocking the event loop/ only this coroutine waits, not entire program)
            await asyncio.to_thread(sem_UI.acquire)
            
            # Get response from queue
            response = comm_queue.get()
            
            # Set event to signal response is ready
            response_ready.set()
            
            return response
        
        # Start login process in a separate thread to avoid blocking UI
        task = asyncio.create_task(handle_login_flow())
        
        # Wait for login to complete (non-blocking for UI)
        await response_ready.wait()
        
        # Get results from task
        response = await task
        
        # Process response
        message = response.get("message")
        
        if "login" in response:
            if not response.get("login"):  # bad credentials
                # Clear input fields
                self.query_one("#username").value = ""
                self.query_one("#password").value = ""
                self.query_one("#IP").value = ""
                self.post_message(LoginMsg(False, message))
            else:
                # Signal driver to continue
                sem_driver.release()
                Logger.log("Login OK.")
                self.post_message(LoginMsg(True, message))
        else:  # web error
            # Clear input fields
            self.query_one("#username").value = ""
            self.query_one("#password").value = ""
            self.query_one("#IP").value = ""
            self.post_message(LoginMsg(False, message))
        
        Logger.log(f'message parsed: {message}')
    
    @on(LoginMsg)
    def handle_login_result(self, message: LoginMsg):
        """Handle login result message"""
        if message.success:
            self.app.push_screen(OptionsScreen())
        
        # Update info message with login result
        self.info_msg = message.message


    # TO BE REMOVED / MODIFIED
    @on(Checkbox.Changed, "#checkbox-ipfiles")
    def on_check_batch(self, event: Checkbox.Changed) -> None:
        """Handle batch checkbox changes"""
        if event.value:
            batch_label = self.query_one("#optional-batch", Static)
            batch_label.update("Path to batch file:")