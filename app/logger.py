import os
import logging
from logging import LogRecord
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('api_logger')
    
    # Check if the logger already has handlers to avoid adding multiple handlers
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)

        # Create formatter
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Create rotating file handler
        max_bytes = 10485760  # 10 MB
        backup_count = 5
        file_handler = RotatingFileHandler('api.log', maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setFormatter(formatter)

        # Add file handler to logger
        logger.addHandler(file_handler)
        
        logger.propagate = False  # Prevent logging from being propagated to the root logger

    return logger

# Instantiate the logger
logger = setup_logger()

