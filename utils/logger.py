# utils/logger.py
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.logging import RichHandler
import json

class CustomLogger:
    def __init__(self, name: str = "sdk_assistant"):
        self.logger = logging.getLogger(name)
        self.setup_logger()
        
    def setup_logger(self, log_file: Optional[str] = None):
        """Set up logger with both file and console handlers"""
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Create formatters
        console_formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Console handler with Rich
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_level=True
        )
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if not log_file:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / f"sdk_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
    def log_command(self, command: str, result: dict):
        """Log command execution with structured data"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "exit_code": result.get("exit_code"),
            "execution_time": result.get("execution_time"),
            "output_length": len(result.get("output", "")),
            "error_length": len(result.get("error", ""))
        }
        
        self.logger.info(f"Command executed: {json.dumps(log_entry)}")
        
        if result.get("exit_code") != 0:
            self.logger.error(f"Command failed: {result.get('error')}")
    
    def log_error(self, error_info: dict):
        """Log error information with context"""
        self.logger.error(
            f"Error occurred:\n"
            f"Type: {error_info.get('error_type')}\n"
            f"Message: {error_info.get('error_message')}\n"
            f"Context: {json.dumps(error_info.get('context', {}))}"
        )
    
    def log_analysis(self, analysis_result: dict):
        """Log analysis results"""
        self.logger.info(
            f"Analysis completed:\n"
            f"Type: {analysis_result.get('type')}\n"
            f"Confidence: {analysis_result.get('confidence')}\n"
            f"Summary: {analysis_result.get('summary')}"
        )
    
    def log_github_action(self, action: str, result: dict):
        """Log GitHub-related actions"""
        self.logger.info(
            f"GitHub {action}:\n"
            f"Status: {result.get('status')}\n"
            f"URL: {result.get('url')}\n"
            f"Details: {json.dumps(result.get('details', {}))}"
        )

def setup_logger(name: str = "sdk_assistant") -> logging.Logger:
    """Convenience function to create and return a logger instance"""
    custom_logger = CustomLogger(name)
    return custom_logger.logger