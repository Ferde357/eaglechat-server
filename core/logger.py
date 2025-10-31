import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
import glob
from .config import settings


class DailyFileHandler(TimedRotatingFileHandler):
    """Custom handler for daily log rotation with YYYYMMDD_LOG.log naming"""
    
    def __init__(self, log_dir: str, retention_days: int):
        self.log_dir = log_dir
        self.retention_days = retention_days
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate filename for today
        filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}_LOG.log")
        
        super().__init__(
            filename=filename,
            when='midnight',
            interval=1,
            backupCount=0  # We'll handle cleanup ourselves
        )
        
        # Set custom naming format
        self.namer = self._custom_namer
        self.rotator = self._custom_rotator
    
    def _custom_namer(self, default_name: str) -> str:
        """Generate custom filename for rotated logs"""
        # Extract the directory and create new filename with tomorrow's date
        dir_name = os.path.dirname(default_name)
        tomorrow = datetime.now() + timedelta(days=1)
        return os.path.join(dir_name, f"{tomorrow.strftime('%Y%m%d')}_LOG.log")
    
    def _custom_rotator(self, source: str, dest: str) -> None:
        """Rotate log file and clean up old logs"""
        # The current log is already named correctly, so we just need to clean up
        self._cleanup_old_logs()
        
        # Create new file for tomorrow
        self.baseFilename = dest
        self.stream = self._open()
    
    def _cleanup_old_logs(self) -> None:
        """Remove log files older than retention_days"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        pattern = os.path.join(self.log_dir, "*_LOG.log")
        
        for log_file in glob.glob(pattern):
            try:
                # Extract date from filename
                filename = os.path.basename(log_file)
                date_str = filename.split('_')[0]
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date < cutoff_date:
                    os.remove(log_file)
                    print(f"Removed old log file: {log_file}")
            except (ValueError, IndexError):
                # Skip files that don't match our naming pattern
                continue


def setup_logger(name: str = __name__) -> logging.Logger:
    """Set up logger with console and file handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.logging.level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.logging.level))
    
    # File handler with daily rotation
    file_handler = DailyFileHandler(
        log_dir=settings.logging.log_directory,
        retention_days=settings.logging.retention_days
    )
    file_handler.setLevel(getattr(logging, settings.logging.level))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Create default logger
logger = setup_logger("eaglechat")


class ContextLogger:
    """Enhanced logger with request context tracking"""
    
    def __init__(self, base_logger=None):
        self.base_logger = base_logger or logger
        self.request_context = {}
    
    def set_context(self, **kwargs):
        """Set context variables for subsequent log messages"""
        self.request_context.update(kwargs)
    
    def clear_context(self):
        """Clear all context variables"""
        self.request_context.clear()
    
    def _format_message(self, message, extra_context=None):
        """Format message with context"""
        context = self.request_context.copy()
        if extra_context:
            context.update(extra_context)
        
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            return f"{message} | Context: {context_str}"
        return message
    
    def debug(self, message, **extra_context):
        """Log debug message with context"""
        self.base_logger.debug(self._format_message(message, extra_context))
    
    def info(self, message, **extra_context):
        """Log info message with context"""
        self.base_logger.info(self._format_message(message, extra_context))
    
    def warning(self, message, **extra_context):
        """Log warning message with context"""
        self.base_logger.warning(self._format_message(message, extra_context))
    
    def error(self, message, **extra_context):
        """Log error message with context"""
        self.base_logger.error(self._format_message(message, extra_context))
    
    def critical(self, message, **extra_context):
        """Log critical message with context"""
        self.base_logger.critical(self._format_message(message, extra_context))
    
    def log_api_call(self, method, endpoint, status_code=None, duration=None, **kwargs):
        """Log API call with standardized format"""
        context = {
            'method': method,
            'endpoint': endpoint,
            'duration_ms': duration,
            **kwargs
        }
        
        if status_code:
            context['status'] = status_code
            if status_code >= 400:
                self.error(f"API call failed: {method} {endpoint}", **context)
            else:
                self.info(f"API call: {method} {endpoint}", **context)
        else:
            self.info(f"API call started: {method} {endpoint}", **context)
    
    def log_ai_request(self, model, input_tokens=None, output_tokens=None, duration=None, **kwargs):
        """Log AI service request with standardized format"""
        context = {
            'ai_model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'duration_ms': duration,
            **kwargs
        }
        
        self.info(f"AI request: {model}", **context)
    
    def log_tenant_activity(self, tenant_id, action, **kwargs):
        """Log tenant-specific activity"""
        context = {
            'tenant_id': tenant_id,
            'action': action,
            **kwargs
        }
        
        self.info(f"Tenant activity: {action}", **context)
    
    def log_performance(self, operation, duration, **kwargs):
        """Log performance metrics"""
        context = {
            'operation': operation,
            'duration_ms': duration,
            **kwargs
        }
        
        level = 'warning' if duration > 5000 else 'info'  # Warn if over 5 seconds
        getattr(self, level)(f"Performance: {operation}", **context)


# Create enhanced logger instance
context_logger = ContextLogger(logger)