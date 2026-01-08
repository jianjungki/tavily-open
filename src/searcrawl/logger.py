# -*- coding: utf-8 -*-
"""
Logger Module - Provides unified logging functionality

This module provides unified logging functionality for the entire application
using loguru library.
"""

from typing import Optional
from loguru import logger
import sys

# Default log format
DEFAULT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger(level: str = "INFO", log_format: Optional[str] = None) -> None:
    """
    Configure application logger

    Args:
        level: Log level, options: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_format: Log format, uses default format if None
    """
    # Remove default handler
    logger.remove()
    
    # Add custom handler with format
    logger.add(
        sys.stdout,
        format=log_format or DEFAULT_LOG_FORMAT,
        level=level.upper(),
        colorize=True
    )


# Set up logger with defaults on module import
setup_logger()


# Export convenience functions
def debug(msg: str, *args, **kwargs) -> None:
    """Log DEBUG level message"""
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Log INFO level message"""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log WARNING level message"""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log ERROR level message"""
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """Log CRITICAL level message"""
    logger.critical(msg, *args, **kwargs)