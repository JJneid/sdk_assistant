# sdk_assistant/__init__.py
from typing import Dict, Any
import logging
import os
from dotenv import load_dotenv

from .core.command_tracker import CommandTracker
from .core.error_handler import ErrorHandler
from .core.github_manager import GitHubManager
from .agents.command_analyzer import CommandAnalyzerAgent
from .agents.doc_generator import DocGeneratorAgent
from .agents.error_analyst import ErrorAnalystAgent
from .agents.web_scraper import WebScraperAgent
from .utils.logger import setup_logger

__version__ = "0.1.0"

logger = setup_logger(__name__)

class SDKAssistant:
    """Main SDK Assistant class that coordinates all components."""
    
    def __init__(self, config: Dict[str, Any] = None):
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.config = config or {}
        
        # Add API keys to config
        self.config["openai"] = {
            **(self.config.get("openai", {})),
            "api_key": os.getenv("OPENAI_API_KEY")
        }
        
        self.config["anthropic"] = {
            **(self.config.get("anthropic", {})),
            "api_key": os.getenv("ANTHROPIC_API_KEY")
        }
        
        # Verify API keys
        if not self.config["openai"]["api_key"]:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        if not self.config["anthropic"]["api_key"]:
            raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable.")
        
        # Initialize components
        self.command_tracker = CommandTracker()
        self.error_handler = ErrorHandler()
        self.github_manager = GitHubManager()
        
        # Initialize AI agents
        self.command_analyzer = CommandAnalyzerAgent(self.config["openai"])
        self.doc_generator = DocGeneratorAgent(self.config["openai"])
        self.error_analyst = ErrorAnalystAgent(self.config["openai"])
        self.web_scraper = WebScraperAgent(self.config)
        
        self.session_active = False
        self.session_data = {}
        
        logger.info("SDK Assistant initialized")

    async def start_session(self, description: str, context: Dict[str, Any] = None) -> None:
        """Start a new SDK testing session."""
        if self.session_active:
            raise RuntimeError("Session already active")
            
        self.session_active = True
        self.session_data = {
            "description": description,
            "context": context or {},
            "commands": [],
            "errors": [],
            "start_time": None,
            "end_time": None
        }
        
        logger.info(f"Started new session: {description}")

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute and track a command."""
        if not self.session_active:
            raise RuntimeError("No active session")
            
        try:
            # Track command
            result = await self.command_tracker.track_command(command)
            
            # Analyze command
            analysis = await self.command_analyzer.analyze_command(
                command,
                result.get("output", "")
            )
            
            # Handle errors if any
            if result.get("exit_code") != 0:
                await self._handle_error(command, result)
            
            # Update session data
            self.session_data["commands"].append({
                "command": command,
                "result": result,
                "analysis": analysis
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            raise

    async def close_session(self) -> None:
        """Close the current session."""
        if not self.session_active:
            raise RuntimeError("No active session")
            
        self.session_active = False
        logger.info("Session closed")