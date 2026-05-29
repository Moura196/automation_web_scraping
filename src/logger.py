"""
Logging configuration for Web Scraping Project
Provides structured logging for scraping operations, errors, and data processing
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors"""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format the message
        if record.levelname == 'CRITICAL':
            fmt = f'{log_color}[%(levelname)s] %(message)s{self.RESET}'
        else:
            fmt = f'{log_color}%(levelname)-8s{self.RESET} | %(asctime)s | %(name)s | %(message)s'
        
        self._style._fmt = fmt
        return super().format(record)


def setup_logger(name: str, log_file: Optional[str] = None, 
                level: int = logging.INFO) -> logging.Logger:
    """
    Setup and configure logger for the application.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file (if None, only console output)
        level: Logging level (default INFO)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger(__name__, 'logs/scraping.log')
        >>> logger.info('Starting scrape...')
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger by name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
    """
    return logging.getLogger(name)


# Create default logger for the module
DEFAULT_LOGGER = setup_logger('web_scraping', log_file='logs/app.log')


class LogContext:
    """Context manager for logging operation sections"""
    
    def __init__(self, logger: logging.Logger, message: str, level: int = logging.INFO):
        self.logger = logger
        self.message = message
        self.level = level
    
    def __enter__(self):
        """Log start of context"""
        self.logger.log(self.level, f'▶ {self.message}...')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log end of context"""
        if exc_type is not None:
            self.logger.error(f'✗ {self.message} failed: {exc_val}')
        else:
            self.logger.log(self.level, f'✓ {self.message} completed')
        return False


# Module-level convenience functions
def info(message: str, logger: Optional[logging.Logger] = None):
    """Log info message"""
    (logger or DEFAULT_LOGGER).info(message)


def warning(message: str, logger: Optional[logging.Logger] = None):
    """Log warning message"""
    (logger or DEFAULT_LOGGER).warning(f'⚠️  {message}')


def error(message: str, logger: Optional[logging.Logger] = None):
    """Log error message"""
    (logger or DEFAULT_LOGGER).error(f'❌ {message}')


def debug(message: str, logger: Optional[logging.Logger] = None):
    """Log debug message"""
    (logger or DEFAULT_LOGGER).debug(message)


def critical(message: str, logger: Optional[logging.Logger] = None):
    """Log critical message"""
    (logger or DEFAULT_LOGGER).critical(f'🚨 {message}')
