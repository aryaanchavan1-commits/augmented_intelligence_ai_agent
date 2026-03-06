"""
Logging Configuration Module
Provides centralized logging for the Augmented Intelligence Agent
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOGS_DIR / "app.log"

# Configure logging format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(user)-15s | %(action)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Custom formatter
class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + LOG_FORMAT + reset,
        logging.INFO: blue + LOG_FORMAT + reset,
        logging.WARNING: yellow + LOG_FORMAT + reset,
        logging.ERROR: red + LOG_FORMAT + reset,
        logging.CRITICAL: bold_red + LOG_FORMAT + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=DATE_FORMAT)
        return formatter.format(record)


class User:
    """UserLogger-aware logger that tracks user actions"""
    
    def __init__(self, name: str = "AugIntel"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler (all logs)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (info and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(CustomFormatter())
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _add_user_context(self, user: str, action: str):
        """Add user context to log record"""
        return {"user": user, "action": action}
    
    def debug(self, message: str, user: str = "system", action: str = "debug"):
        self.logger.debug(message, extra=self._add_user_context(user, action))
    
    def info(self, message: str, user: str = "system", action: str = "info"):
        self.logger.info(message, extra=self._add_user_context(user, action))
    
    def warning(self, message: str, user: str = "system", action: str = "warning"):
        self.logger.warning(message, extra=self._add_user_context(user, action))
    
    def error(self, message: str, user: str = "system", action: str = "error"):
        self.logger.error(message, extra=self._add_user_context(user, action))
    
    def critical(self, message: str, user: str = "system", action: str = "critical"):
        self.logger.critical(message, extra=self._add_user_context(user, action))
    
    def log_login(self, username: str, success: bool, ip: str = "unknown"):
        """Log login attempt"""
        status = "SUCCESS" if success else "FAILED"
        action = "login_success" if success else "login_failed"
        message = f"Login {status} - Username: {username}, IP: {ip}"
        if success:
            self.info(message, user=username, action=action)
        else:
            self.warning(message, user=username, action=action)
    
    def log_logout(self, username: str):
        """Log logout"""
        self.info(f"User logged out", user=username, action="logout")
    
    def log_api_call(self, username: str, model: str, tokens_used: int = 0):
        """Log API call to Groq"""
        self.info(
            f"Groq API call - Model: {model}, Tokens: {tokens_used}",
            user=username,
            action="api_call"
        )
    
    def log_error(self, username: str, error: Exception, context: str = ""):
        """Log error with context"""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        self.error(error_msg, user=username, action="error")
    
    def log_workflow(self, username: str, workflow: str, step: str, status: str):
        """Log workflow execution"""
        self.info(
            f"Workflow: {workflow} - Step: {step} - Status: {status}",
            user=username,
            action=f"workflow_{status}"
        )


# Create singleton instance
app_logger = User()


def get_logger() -> User:
    """Get the application logger instance"""
    return app_logger
