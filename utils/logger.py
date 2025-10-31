"""
Centralized logging configuration for TALAIT_BOT
Provides automatic log rotation every 3 days with structured logging
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path


class BotLogger:
    """Centralized logger configuration with automatic rotation"""

    _loggers = {}
    _initialized = False

    @classmethod
    def setup(cls, log_level: str = "INFO", retention_days: int = 3):
        """
        Initialize the logging system with rotation handlers

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            retention_days: Number of days before log rotation (default: 3)
        """
        if cls._initialized:
            return

        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create archives directory for old logs
        archive_dir = log_dir / "archives"
        archive_dir.mkdir(exist_ok=True)

        # Convert log level string to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler (for terminal output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

        # Main Bot Log Handler (rotates every 3 days)
        bot_log_handler = TimedRotatingFileHandler(
            filename=log_dir / "bot.log",
            when='D',  # Rotate daily
            interval=retention_days,  # Every 3 days
            backupCount=7,  # Keep last 7 rotated logs
            encoding='utf-8'
        )
        bot_log_handler.setLevel(numeric_level)
        bot_log_handler.setFormatter(detailed_formatter)
        bot_log_handler.suffix = "%Y-%m-%d_%H-%M-%S"  # Timestamp suffix for rotated files
        root_logger.addHandler(bot_log_handler)

        # Commands Log Handler (tracks all command usage)
        commands_log_handler = TimedRotatingFileHandler(
            filename=log_dir / "commands.log",
            when='D',
            interval=retention_days,
            backupCount=7,
            encoding='utf-8'
        )
        commands_log_handler.setLevel(logging.INFO)
        commands_log_handler.setFormatter(detailed_formatter)
        commands_log_handler.suffix = "%Y-%m-%d_%H-%M-%S"

        # Only log command-related messages to commands.log
        commands_log_handler.addFilter(lambda record: 'command' in record.name.lower() or 'cogs' in record.name.lower())
        root_logger.addHandler(commands_log_handler)

        # Error Log Handler (only errors and critical)
        error_log_handler = TimedRotatingFileHandler(
            filename=log_dir / "errors.log",
            when='D',
            interval=retention_days,
            backupCount=7,
            encoding='utf-8'
        )
        error_log_handler.setLevel(logging.ERROR)
        error_log_handler.setFormatter(detailed_formatter)
        error_log_handler.suffix = "%Y-%m-%d_%H-%M-%S"
        root_logger.addHandler(error_log_handler)

        cls._initialized = True

        # Log initialization
        init_logger = cls.get_logger("logger")
        init_logger.info(f"Logging system initialized | Level: {log_level} | Rotation: every {retention_days} days")
        init_logger.info(f"Logs directory: {log_dir.absolute()}")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger instance

        Args:
            name: Name of the logger (usually module name)

        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)

        return cls._loggers[name]

    @classmethod
    def log_command(cls, command_name: str, user: str, guild: str, success: bool = True):
        """
        Log command execution details

        Args:
            command_name: Name of the executed command
            user: User who executed the command
            guild: Guild where command was executed
            success: Whether command succeeded
        """
        logger = cls.get_logger("commands")
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"/{command_name} | User: {user} | Guild: {guild} | {status}")

    @classmethod
    def log_error(cls, module: str, error: Exception, context: str = ""):
        """
        Log error with full context

        Args:
            module: Module where error occurred
            error: Exception object
            context: Additional context information
        """
        logger = cls.get_logger(module)
        error_msg = f"{error.__class__.__name__}: {str(error)}"
        if context:
            error_msg = f"{context} | {error_msg}"
        logger.error(error_msg, exc_info=True)

    @classmethod
    def log_data_operation(cls, operation: str, file_path: str, success: bool = True):
        """
        Log data file operations

        Args:
            operation: Type of operation (load, save, create, etc.)
            file_path: Path to the data file
            success: Whether operation succeeded
        """
        logger = cls.get_logger("data_manager")
        status = "✓" if success else "✗"
        logger.debug(f"{status} {operation.upper()} | {file_path}")

    @classmethod
    def log_scheduled_task(cls, task_name: str, status: str, details: str = ""):
        """
        Log scheduled task execution

        Args:
            task_name: Name of the scheduled task
            status: Status (started, completed, failed)
            details: Additional details
        """
        logger = cls.get_logger("scheduled_tasks")
        msg = f"Task: {task_name} | Status: {status.upper()}"
        if details:
            msg += f" | {details}"

        if status.lower() == "failed":
            logger.error(msg)
        else:
            logger.info(msg)


def setup_logging(log_level: str = None, retention_days: int = None):
    """
    Convenience function to initialize logging system

    Args:
        log_level: Logging level from environment or default to INFO
        retention_days: Days before rotation from environment or default to 3
    """
    # Get from environment variables if not provided
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    if retention_days is None:
        retention_days = int(os.getenv("LOG_RETENTION_DAYS", "3"))

    BotLogger.setup(log_level=log_level, retention_days=retention_days)


# Convenience function for getting loggers
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    return BotLogger.get_logger(name)