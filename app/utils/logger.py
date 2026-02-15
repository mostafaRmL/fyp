"""
Logging Configuration Module

This module provides a centralized logging configuration with colored output
for better readability during development and debugging.
"""

import logging
import sys
from typing import Optional
import colorlog
from app.config import settings


class LoggerSetup:
    """
    Logger configuration and setup
    
    Provides colored console logging with different formats for
    development and production environments.
    """
    
    _loggers: dict[str, logging.Logger] = {}
    
    @staticmethod
    def get_logger(name: str = "medical_assistant") -> logging.Logger:
        """
        Get or create a configured logger instance
        
        Args:
            name: Logger name (typically the module name)
            
        Returns:
            Configured logger instance
        """
        if name in LoggerSetup._loggers:
            return LoggerSetup._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Color formatter for development
        if settings.is_development:
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s",
                datefmt=None,
                reset=True,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                },
                secondary_log_colors={},
                style='%'
            )
        else:
            # Simple formatter for production
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        LoggerSetup._loggers[name] = logger
        return logger


# Convenience function for getting logger
def get_logger(name: str = "medical_assistant") -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return LoggerSetup.get_logger(name)


# Create default logger instance
logger = get_logger()