import asyncio
from driver import Driver
from terminal import ScreenApp
from logger import Logger
import threading
import syncprims


async def load_driver():
    driver = Driver()
    await driver.init()
    
    listen_t = asyncio.create_task(driver.listen())
    poll_t = asyncio.create_task(driver.chk_for_logout())
    driver_tasks = [listen_t, poll_t]
    await asyncio.gather(*driver_tasks)
    
def run_ui():
    app = ScreenApp()
    app.run()

async def main():
    Logger.configure(log_file="app.log", console=False, level="INFO")

    # Create a thread for the UI 
    # It's a daemon so it exits along with main thread 
    ui_thread = threading.Thread(target=run_ui, daemon=True)             
    ui_thread.start()


    # Run the driver in the asyncio event loop
    try:
        await load_driver()
    except Exception as e:
        Logger.log(f"Critical failure on driver: {e}")


    # Wait for UI thread to complete
    ui_thread.join(timeout=5.0)

if __name__ == '__main__':
    asyncio.run(main())