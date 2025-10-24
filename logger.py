import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
import glob
from config import settings


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