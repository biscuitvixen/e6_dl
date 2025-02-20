""" Global logger configuration for the project """

import logging
import colorlog

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
logger.setLevel(logging.INFO)  # Default log level

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Attach the handler to the logger
logger.addHandler(console_handler)

# Function to dynamically update log level
def set_log_level(level: str):
    """Set the logging level dynamically."""
    level = level.upper()
    if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.setLevel(getattr(logging, level))
        logging.getLogger().setLevel(getattr(logging, level))  # Apply globally
        logger.info(f"Log level set to {level}")
    else:
        logger.warning(f"Invalid log level: {level}. Using default INFO.")
