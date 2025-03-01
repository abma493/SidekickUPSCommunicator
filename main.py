import asyncio
from driver import Driver
from terminal import ScreenApp
from logger import Logger
import threading

async def async_load_driver():
    driver = Driver()
    await driver.init()
    await driver.listen()
    Logger.log("Driver loaded OK.")

def run_ui():
    app = ScreenApp()
    app.run()
    Logger.log("UI loaded OK.")

async def main():
    Logger.configure(log_file="app.log", console=False, level="INFO")
    Logger.log("Loading driver and UI threads...")

    # Create a thread for the UI
    ui_thread = threading.Thread(target=run_ui, daemon=True)
    ui_thread.start()

    # Run the driver in the asyncio event loop
    await async_load_driver()

    # Wait for UI thread to complete
    ui_thread.join()

if __name__ == '__main__':
    asyncio.run(main())