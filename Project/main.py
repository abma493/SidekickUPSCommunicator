import os
import sys
from terminal import ScreenApp
from logger import Logger

def main():
    # Fix CWD so relative paths (ip lists, reports, exports) resolve correctly
    # regardless of where the app is launched from.
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    Logger.configure(log_file="app.log", console=False, level="INFO")
    app = ScreenApp()
    app.run()

if __name__ == '__main__':
    main()