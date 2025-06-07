from common.common_term import *
from screens.BaseScreen import BaseScreen
from driver import Driver
import asyncio
from logger import Logger
      

class ScreenApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self.driver_tasks = []

    async def load_driver(self):
        try:
            await self.driver.init()
            listen_task = asyncio.create_task(self.driver.listen())
            poll_task = asyncio.create_task(self.driver.chk_for_logout())
            self.driver_tasks = [listen_task, poll_task]
        except Exception as e:
            Logger.log(f"Critical failure on driver: {e}")

    async def on_mount(self) -> None:
        self.driver = Driver()
        self.push_screen(BaseScreen())
    
