#!/usr/bin/env python3
"""
Filename: logging_config.py
Description: Centralized logging configuration for PodCam monitoring system
Provides consistent logging setup across all modules with daily rotation
"""

import logging
import sys
import os
import re
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    log_filename: Optional[str] = None,
    level: int = logging.INFO,
    enable_console: bool = True,
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Setup a logger with file and optional console handlers.
    
    Args:
        name (str): Logger name (usually __name__ from the calling module)
        log_filename (str, optional): Name of log file (without path). 
                                     If None, uses module name + '.log'
        level (int): Logging level (default: logging.INFO)
        enable_console (bool): Enable console output (default: True)
        log_format (str): Log message format string
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # If handlers exist from prior setup, we'll validate and add missing ones
    
    # Create logs directory relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Determine log filename
    if log_filename is None:
        # Use module name as log filename
        module_name = name.split('.')[-1] if '.' in name else name
        log_filename = f"{module_name}.log"
    
    # Configure log formatter
    log_formatter = logging.Formatter(log_format)
    
    # File handler with daily rotation, keep 7 days
    log_file_path = os.path.join(logs_dir, log_filename)
    # Add file handler if missing (daily rotation, keep 7 days)
    have_file_handler = any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers)
    if not have_file_handler:
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(log_formatter)
        # Add date to rotated log files with .log extension
        file_handler.suffix = ".%Y-%m-%d.log"
        file_handler.extMatch = re.compile(r"^\.\d{4}-\d{2}-\d{2}\.log$")
        logger.addHandler(file_handler)
    
    # Console handler (optional)
    if enable_console:
        have_console_handler = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        if not have_console_handler:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)
    
    # Ensure logging level is set
    logger.setLevel(level)
    
    # Prevent propagation to avoid duplicate messages
    logger.propagate = False
    
    return logger


def setup_email_logger(enable_console: bool = False) -> logging.Logger:
    """
    Setup logger specifically for email notifications.
    
    Args:
        enable_console (bool): Enable console output (default: False for module import)
    
    Returns:
        logging.Logger: Configured email logger
    """
    return setup_logger(
        name="email_notification",
        log_filename="email_notification.log",
        enable_console=enable_console,
        log_format="%(asctime)s [%(levelname)s] %(message)s"
    )


def setup_sensor_logger() -> logging.Logger:
    """
    Setup logger for sensor monitoring service.
    
    Returns:
        logging.Logger: Configured sensor logger
    """
    return setup_logger(
        name="sensors_ts",
        log_filename="sensors_ts.log",
        enable_console=True
    )


def setup_bme680_logger(enable_console: bool = True) -> logging.Logger:
    """
    Setup logger for BME680 sensor module.
    
    Args:
        enable_console (bool): Enable console output (default: True for main, False for import)
    
    Returns:
        logging.Logger: Configured BME680 logger
    """
    return setup_logger(
        name="bme680_ts",
        log_filename="bme680_ts.log",
        enable_console=enable_console
    )


def setup_speedtest_logger(logger_name: str = "speedtest_logger") -> logging.Logger:
    """
    Setup logger for speedtest monitoring.
    
    Args:
        logger_name (str): Logger name (default: "speedtest_logger")
    
    Returns:
        logging.Logger: Configured speedtest logger
    """
    return setup_logger(
        name=logger_name,
        log_filename=f"{logger_name}.log",
        enable_console=True
    )


# Convenience function for generic module logging
def get_logger(module_name: str, enable_console: bool = True) -> logging.Logger:
    """
    Get a configured logger for any module.
    
    Args:
        module_name (str): Module name (usually __name__)
        enable_console (bool): Enable console output (default: True)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(
        name=module_name,
        enable_console=enable_console
    )
