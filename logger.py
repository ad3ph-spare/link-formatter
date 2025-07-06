# logger.py
import sys
import os
from loguru import logger

# Define a default log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Create the directory if it doesn't exist

# Configure Loguru logger
logger.remove()  # Remove default handler (stdout)

# Add a handler to write logs to a file
log_file_path = os.path.join(LOG_DIR, "app.log")
logger.add(
    log_file_path,
    rotation="500 MB",  # Rotate log file if it reaches 500MB
    retention="10 days",  # Keep logs for 10 days
    compression="zip",    # Compress rotated logs
    level="INFO",         # Default log level for file logs
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}.{function}:{line} - {message}",
    enqueue=True,         # Asynchronously write logs for better performance
)

# Add a handler to print logs to the console (stdout)
logger.add(
    sys.stdout,
    level="DEBUG",        # Default log level for console logs (can be different from file)
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Optional: Set a default log level for the entire logger if not specified in handlers
logger.level("INFO") # You can set a global level, but handlers levels usually take precedence


# Now you can import and use 'logger' in other modules

def test_logger()->None:    # Example usage of the logger within logger.py itself
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("An exception occurred!")

    # Example of using contextual logging
    with logger.contextualize(user="example_user", request_id="12345"):
        logger.info("Processing a request for user {user} with ID {request_id}")
        logger.debug("Detailed information about the request.")

if __name__ == "__main__":
    test_logger()
