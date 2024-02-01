import os
import logging
from logging.handlers import RotatingFileHandler

# get current path
current_path = os.path.dirname(os.path.abspath(__file__))

# add path to log directory
log_directory = os.path.join(current_path, "logs")

# Create the directory if it does not exist
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Set up the logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Define the full path for the log file
info_log_path = os.path.join(log_directory, 'info.log')
error_log_path = os.path.join(log_directory, 'error.log')

# Set up the logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # This will capture all levels of messages

# Handler for rotating informational (INFO) logs
info_handler = RotatingFileHandler(info_log_path, maxBytes=1024*1024*5, backupCount=5)
info_handler.setLevel(logging.INFO)  # Set the level for this handler
info_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
info_handler.setFormatter(info_formatter)
info_handler.addFilter(lambda record: record.levelno <= logging.INFO)  # Only INFO and below

# Handler for permanent warning and error logs
error_handler = logging.FileHandler(error_log_path)
error_handler.setLevel(logging.WARNING)  # Set the level for this handler
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)

# Add handlers to the logger
logger.addHandler(info_handler)
logger.addHandler(error_handler)


if __name__ == '__main__':
    # only for testing
    logger.info('This is an informational message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')

    print('done')

