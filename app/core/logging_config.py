"""
Centralized logging configuration for the Fashion Backend API.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, ClassVar
from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS: ClassVar[dict[str, str]] = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        """
        Format the given LogRecord and apply ANSI color codes to its level name when a mapping exists.
        
        If the record's level name is present in the formatter's color map, `record.levelname` is replaced with a colorized version before delegating to the base formatter.
        
        Parameters:
            record (logging.LogRecord): The log record to format.
        
        Returns:
            str: The formatted log message.
        """
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure the central "fashion_backend" logger with console and optional rotating file handlers.
    
    Parameters:
        log_level (str): Logging level name (e.g., "DEBUG", "INFO").
        log_file (Optional[str]): Path to a log file; when provided, a RotatingFileHandler is attached and parent directories are created.
        console_output (bool): If True, attach a stdout StreamHandler with colored level names.
        max_file_size (int): Maximum size in bytes before rotating the log file.
        backup_count (int): Number of rotated backup files to keep.
    
    Returns:
        logging.Logger: The configured logger instance named "fashion_backend".
    """
    # Create logger
    logger = logging.getLogger("fashion_backend")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a namespaced logger scoped under the "fashion_backend" package.
    
    Parameters:
        name (str): Module-specific logger name appended to the "fashion_backend." namespace.
    
    Returns:
        logging.Logger: Logger instance named "fashion_backend.{name}".
    """
    return logging.getLogger(f"fashion_backend.{name}")


# Default logger setup
def configure_default_logging():
    """
    Configure and return the application's default logger using settings-derived values.
    
    Reads LOG_LEVEL (default "INFO") and LOG_FILE (default "logs/fashion_backend.log") from the application settings, then calls setup_logging with console output enabled.
    
    Returns:
        logging.Logger: A logger named "fashion_backend" configured with the resolved log level and optional rotating file handler.
    """
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
    log_file = getattr(settings, 'LOG_FILE', 'logs/fashion_backend.log')
    
    return setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_output=True
    )


# Initialize default logger
default_logger = configure_default_logging()