import logging
import sys
from typing import Optional


# ANSI color codes for consistent logging across all services
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with consistent colors across all services."""

    COLORS = {
        "DEBUG": Colors.DIM + Colors.CYAN,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.BOLD + Colors.RED,
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Colors.END}"

        # Add color to service name if present
        if hasattr(record, "service_name"):
            record.service_name = f"{Colors.BLUE}{record.service_name}{Colors.END}"

        return super().format(record)


def setup_logging(
    service_name: str,
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_to_file: bool = False,
    log_file: str = None,
) -> logging.Logger:
    """
    Setup unified logging configuration for the service.

    Args:
        service_name: Name of the service (e.g., "traffic_storage", "traffic_control")
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format string
        log_to_file: Whether to log to file in addition to console
        log_file: Log file path if log_to_file is True

    Returns:
        Configured logger instance
    """
    # Default format if not provided
    if format_string is None:
        format_string = "%(asctime)s - %(levelname)s - [%(service_name)s] - %(name)s - %(message)s"

    # Default log file if not provided
    if log_file is None:
        log_file = f"{service_name}.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = ColoredFormatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        file_handler = logging.FileHandler(log_file)
        # Use non-colored formatter for file
        file_formatter = logging.Formatter(
            format_string.replace("%(levelname)s", "%(levelname)s").replace(
                "%(service_name)s", "%(service_name)s"
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Set specific logger levels for external libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Create and return service logger
    logger = logging.getLogger(service_name)

    # Add service name to log records
    class ServiceFilter(logging.Filter):
        def filter(self, record):
            record.service_name = service_name
            return True

    logger.addFilter(ServiceFilter())

    # Log startup message
    logger.info(f"Logging configured for {service_name} with level: {level}")

    return logger


def get_logger(name: str, service_name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)
        service_name: Service name for coloring (optional)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Add service name filter if provided
    if service_name:

        class ServiceFilter(logging.Filter):
            def filter(self, record):
                record.service_name = service_name
                return True

        # Only add filter if not already present
        if not any(isinstance(f, ServiceFilter) for f in logger.filters):
            logger.addFilter(ServiceFilter())

    return logger


# Convenience functions for common log messages
def log_request(
    logger: logging.Logger, method: str, url: str, status_code: int = None, duration: float = None
):
    """Log HTTP request information."""
    if status_code and duration:
        logger.info(f"Request: {method} {url} - Status: {status_code} - Duration: {duration:.3f}s")
    else:
        logger.info(f"Request: {method} {url}")


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """Log error with context."""
    error_msg = f"Error in {context}: {str(error)}" if context else str(error)
    logger.error(error_msg)


def log_success(logger: logging.Logger, operation: str, details: str = ""):
    """Log successful operation."""
    success_msg = f"Success: {operation}"
    if details:
        success_msg += f" - {details}"
    logger.info(success_msg)


def log_warning(logger: logging.Logger, message: str, context: str = ""):
    """Log warning with context."""
    warning_msg = f"Warning in {context}: {message}" if context else message
    logger.warning(warning_msg)
