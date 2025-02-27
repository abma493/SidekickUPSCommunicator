from driver import Driver
from threading import Thread
from terminal import ScreenApp
from logger import Logger

def load_driver():
	driver = Driver()
	driver.init()
	driver.listen()


def load_ui():
    app = ScreenApp()
    app.run()

def main():
	Logger.configure(log_file="app.log", console=False, level="INFO")
	Logger.log("Loading driver and UI threads...")
	driver_thread = Thread(target=load_driver)
	ui_thread = Thread(target=load_ui)
	
	driver_thread.start()
	Logger.log("Driver loaded OK.")
	ui_thread.start()
	Logger.log("UI loaded OK.")

	driver_thread.join()
	ui_thread.join()


if __name__ == '__main__':
	main()
