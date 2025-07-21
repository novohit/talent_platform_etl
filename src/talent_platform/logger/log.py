import logging
import logging.handlers
from pathlib import Path
import colorlog


def setup_logger(name: str = "talent_platform_etl") -> logging.Logger:
    """
    Setup and configure logger

    Args:
        name: Logger name, defaults to 'talent_platform_etl'

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Color console formatter
    console_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }

    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s%(reset)s",
        log_colors=console_colors,
        reset=True,
        style="%",
    )

    # File handler (with rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # Error file handler
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)

    # Console handler with colors
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)

    # 禁止日志传播到父级导致打印重复的日志，Celery 执行任务时会有一个专用的任务日志器
    #2025-07-21 14:31:05,110 - INFO - Executing plugin mysql_test with parameters: []  │
    #[2025-07-21 14:31:05,110: INFO/ForkPoolWorker-5] Executing plugin mysql_test with parameters: []
    
    logger.propagate = False

    return logger


# Create default logger instance
logger = setup_logger()
