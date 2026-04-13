import logging
import logging.handlers
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from core.config import settings


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

    In production (ENV=production): logs are written to stdout only, using the
    JSON formatter. File handlers are skipped — container filesystems are ephemeral
    and platforms collect stdout logs directly (12-Factor App pattern).

    In development: logs go to stdout (human-readable) and to rotating files
    (app.log for all levels, error.log for errors only).

    Args:
        log_level: Minimum log level for the console handler (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files. Only used in development.
    """

    # Step 1: Create logs directory — development only (not needed in production)
    log_path = Path(log_dir)
    if settings.ENV != "production":
        log_path.mkdir(exist_ok=True)

    # Step 2: Convert string log level to logging constant
    # "INFO" -> logging.INFO (which is the number 20)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Step 3: Create formatters
    # JSON formatter: structured output for machines/log aggregators (used in production)
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(message)s'
    )
    # Console formatter: human-readable output for development
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Step 4: Create console handler (stdout) — used in both environments
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)  # Respects LOG_LEVEL from .env

    # Step 5: Create file handlers — development only
    if settings.ENV != "production":
        # All logs with rotation (10 MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File captures everything
        file_handler.setFormatter(json_formatter)

        # Errors only (ERROR and CRITICAL)
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)

    # Step 6: Configure root logger
    # The root logger sits at the top of the logger tree. All loggers created with
    # logging.getLogger(__name__) propagate their records up to the root, so attaching
    # handlers here means every module in the app uses the same output configuration.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything — handlers filter by level
    root_logger.handlers.clear()  # Avoid duplicate handlers if setup_logging is called twice

    if settings.ENV == "production":
        # Production: stdout only, JSON format (platform captures stdout)
        console_handler.setFormatter(json_formatter)
        root_logger.addHandler(console_handler)
    else:
        # Development: human-readable stdout + rotating file handlers
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)

    # Step 7: Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)
    logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.WARNING)

    root_logger.info("Logging configured", extra={"log_level": log_level})



def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)