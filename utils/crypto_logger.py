import logging

# Define the log file path
log_file = 'script.log'

# Set up the basic configuration for logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S',  # Date format
    handlers=[
        logging.FileHandler(log_file),  # Log to the specified file
        logging.StreamHandler()  # Optionally log to the console
    ]
)

# Get a logger instance
logger = logging.getLogger(__name__)