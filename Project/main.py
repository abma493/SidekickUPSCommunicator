from terminal import ScreenApp
from logger import Logger

def main():
    Logger.configure(log_file="app.log", console=False, level="INFO")
    app = ScreenApp()
    app.run()

if __name__ == '__main__':
    main()