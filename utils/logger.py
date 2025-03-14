import logging
import sys
from utils.config_loader import config

# Create a global logger
logger = logging.getLogger("AppLogger")
logger.setLevel(logging.INFO)  # Set logging level

# Remove any existing handlers to avoid duplicates
if logger.hasHandlers():
    logger.handlers.clear()

# Check configuration for logging preference
log_to_console = config.get("log_to_console", True)

# Create the appropriate handler (console or file)
if log_to_console:
    handler = logging.StreamHandler(sys.stdout)  # Logs to console
else:
    handler = logging.FileHandler("app.log")  # Logs to a file

# Define log format with class name, method, and line number
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s()] %(message)s"
)
#formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)
