import os
import sys
import logging
import logging.handlers
import json
import datetime
from pathlib import Path

# --- Determine Project Root ---
# This file is in symphony/, so project root is one level up.
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

class StructuredJSONFormatter(logging.Formatter):
    """A custom formatter to output logs as a single line of JSON."""
    def format(self, record):
        # Ensure 'details' key exists for all records
        if not hasattr(record, 'details'):
            record.details = {}
        
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "agent": record.name,
            "event": record.msg, # Use the log message as the event name
            "details": record.details
        }
        return json.dumps(log_entry)

# --- Global State ---
_loggers_configured = set()

def setup_logging():
    """One-time setup for the root logger and log directory."""
    LOG_DIR.mkdir(exist_ok=True)
    
    # Configure the root logger to prevent unhandled messages
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Prevent default handlers from being added if they already exist
    if not root_logger.handlers:
        # A simple handler for root logger messages, if any
        root_handler = logging.StreamHandler()
        root_handler.setLevel(logging.ERROR) # Only show critical errors from root
        root_formatter = logging.Formatter('ROOT-ERROR: %(message)s')
        root_handler.setFormatter(root_formatter)
        root_logger.addHandler(root_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance with structured file and console output.
    This function is idempotent; it will only configure a logger once.
    """
    if name in _loggers_configured:
        return logging.getLogger(name)

    # Ensure the log directory exists
    setup_logging()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO) # Capture INFO and above for the file

    # Prevent propagation to the root logger to avoid duplicate messages
    logger.propagate = False

    # --- 1. File Handler for Structured JSON Logs ---
    log_file_path = LOG_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024, # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(file_handler)

    # --- 2. Console Handler for Clean Output ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING) # Only show warnings/errors on console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Mark this logger as configured
    _loggers_configured.add(name)
    
    return logger