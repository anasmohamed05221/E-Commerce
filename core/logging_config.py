import logging
import logging.handlers
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom formatter that adds standard fields to every log entry.
    """
    def add_fields(self, log_record, record, message_dict):
        """
        Called for every log entry to add custom fields.
        
        Args:
            log_record: The dict that will become JSON (we modify this)
            record: The original LogRecord object (has all log info)
            message_dict: The message and any 'extra' fields
        """
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        log_record['timestamp'] = record.created  # Unix timestamp (when log was created)
        log_record['level'] = record.levelname    # DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_record['logger'] = record.name        # Logger name (e.g., 'routers.auth')
        log_record['module'] = record.module      # Module name (e.g., 'auth')
        log_record['function'] = record.funcName  # Function name where log was called
        log_record['line'] = record.lineno        # Line number where log was called




def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configure application-wide logging.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory where log files will be stored
    """

    # Step 1: Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Step 2: Convert string log level to logging constant
    # "INFO" -> logging.INFO (which is the number 20)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)


    # Step 3: Create formatters
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(message)s'
    )


    # Console formatter - more human-readable for development
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


    # Step 4: Create Console Handler (outputs to terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)  # Respects LOG_LEVEL from .env
    console_handler.setFormatter(console_formatter)


    # Step 5: Create File Handler - all logs (with rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,               # Keep 5 old files (app.log.1, app.log.2, etc.)
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # File captures everything
    file_handler.setFormatter(json_formatter)
    
    # Step 6: Create Error File Handler - only errors (with rotation)
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL
    error_handler.setFormatter(json_formatter)



    # Step 7: Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter
    
    # Remove existing handlers (important if setup_logging is called multiple times)
    root_logger.handlers.clear()
    
    # Step 8: Add all handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Step 9: Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)  # Silences startup/shutdown messages
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)  # Silences error handler messages
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)
    logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.WARNING)   
    
    # Step 10: Log that logging is configured
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_dir": str(log_path.absolute())
        }
    )



def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)