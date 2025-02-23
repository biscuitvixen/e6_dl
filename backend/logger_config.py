""" Global logger configuration for the project """

import logging
import colorlog
from logging.handlers import RotatingFileHandler

# Define a colorized log format
log_colors = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red'
}

# Create a formatter with color support
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    log_colors=log_colors
)

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Default log level

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Attach the handler to the logger
logger.addHandler(console_handler)

# Create a rotating file handler that logs at the debug level
file_handler = RotatingFileHandler('e6dl.log', maxBytes=10485760, backupCount=5)  # 10MB per file, keep 5 backups
file_handler.setLevel(logging.DEBUG) # All levels will be logged
file_handler.setFormatter(formatter)

# Attach the file handler to the logger
logger.addHandler(file_handler)

# Function to dynamically update log level
def set_log_level(level: str):
    """Set the logging level dynamically."""
    level = level.upper()
    if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.setLevel(getattr(logging, level))
        logging.getLogger().setLevel(getattr(logging, level))  # Apply globally
        logger.debug(f"Log level set to {level}")
    else:
        logger.warning(f"Invalid log level: {level}. Using default.")
