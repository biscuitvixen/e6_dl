import logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Default level (can be overridden)
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# Create a logger instance
logger = logging.getLogger(__name__)

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

