# logger.py
import logging
from threading import Lock

# Module-level lock and state
_global_lock = Lock()
_configured = False

class Logger:


    @staticmethod
    def configure(log_file="app.log", console=True, level=logging.INFO):
        """Configure the logging system once."""
        global _configured
        if not _configured:
            with _global_lock:
                if not _configured:  # Double-check inside lock
                    handlers = [logging.FileHandler(log_file)]
                    if console:
                        handlers.append(logging.StreamHandler())
                    
                    logging.basicConfig(
                        level=level,
                        format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
                        handlers=handlers
                    )
                    # Get asyncio's logger specifically
                    asyncio_logger = logging.getLogger('asyncio')
                    asyncio_logger.setLevel(logging.DEBUG)
                    _configured = True
                    Logger.log("\nLogger configured OK.", level="WARNING")
    
    @staticmethod
    def log(message, level="INFO"):
        """Log a message at the specified level."""
        # Ensure logging is configured
        if not _configured:
            Logger.configure()
            
        # Get the logging function based on level
        log_func = getattr(logging, level.lower(), logging.info)
        log_func(message)