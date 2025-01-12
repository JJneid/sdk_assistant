# utils/helpers.py
import os
import sys
import platform
import subprocess
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import re
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

console = Console()

class CommandHelper:
    @staticmethod
    def parse_command(command: str) -> Dict[str, Any]:
        """Parse a command string to extract components and flags"""
        parts = command.split()
        
        return {
            "executable": parts[0],
            "args": parts[1:],
            "flags": [arg for arg in parts[1:] if arg.startswith("-")],
            "positional_args": [arg for arg in parts[1:] if not arg.startswith("-")]
        }

    @staticmethod
    def get_command_hash(command: str) -> str:
        """Generate a unique hash for a command"""
        return hashlib.md5(command.encode()).hexdigest()

    @staticmethod
    def is_sudo_command(command: str) -> bool:
        """Check if command requires sudo privileges"""
        return command.strip().startswith("sudo")

class SystemHelper:
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get detailed system information"""
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_path": sys.executable
        }

    @staticmethod
    def get_env_info() -> Dict[str, str]:
        """Get relevant environment variables"""
        relevant_vars = [
            "PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
            "GITHUB_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"
        ]
        
        return {
            var: os.environ.get(var, "") 
            for var in relevant_vars 
            if os.environ.get(var)
        }

    @staticmethod
    def is_virtual_env() -> bool:
        """Check if running in a virtual environment"""
        return bool(os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_DEFAULT_ENV"))

class FileHelper:
    @staticmethod
    def ensure_dir(path: str) -> None:
        """Ensure directory exists, create if it doesn't"""
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def safe_write_json(path: str, data: Dict[str, Any]) -> None:
        """Safely write JSON data to file with backup"""
        file_path = Path(path)
        
        # Create backup if file exists
        if file_path.exists():
            backup_path = file_path.with_suffix('.json.bak')
            file_path.rename(backup_path)
        
        # Write new data
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def read_json_safe(path: str) -> Optional[Dict[str, Any]]:
        """Safely read JSON data with backup handling"""
        file_path = Path(path)
        backup_path = file_path.with_suffix('.json.bak')
        
        try:
            with open(file_path) as f:
                return json.load(f)
        except Exception as e:
            if backup_path.exists():
                with open(backup_path) as f:
                    return json.load(f)
            return None

class DisplayHelper:
    @staticmethod
    def display_command_history(commands: List[Dict[str, Any]]) -> None:
        """Display command history in a formatted table"""
        table = Table(title="Command History")
        
        table.add_column("Timestamp", justify="left", style="cyan")
        table.add_column("Command", justify="left", style="green")
        table.add_column("Status", justify="center", style="bold")
        table.add_column("Duration", justify="right", style="yellow")
        
        for cmd in commands:
            status = "✓" if cmd.get("exit_code") == 0 else "✗"
            duration = f"{cmd.get('execution_time', 0):.2f}s"
            
            table.add_row(
                cmd.get("timestamp"),
                cmd.get("command"),
                status,
                duration
            )
        
        console.print(table)

    @staticmethod
    def display_error_analysis(error_analysis: Dict[str, Any]) -> None:
        """Display error analysis results"""
        console.print("\n[bold red]Error Analysis[/bold red]")
        console.print(f"Type: {error_analysis.get('error_type', 'Unknown')}")
        
        if error_analysis.get("solutions"):
            console.print("\n[bold]Potential Solutions:[/bold]")
            for solution in error_analysis["solutions"]:
                console.print(f"• {solution}")
        
        if error_analysis.get("prevention_tips"):
            console.print("\n[bold]Prevention Tips:[/bold]")
            for tip in error_analysis["prevention_tips"]:
                console.print(f"• {tip}")

class ValidationHelper:
    @staticmethod
    def validate_github_token(token: Optional[str]) -> bool:
        """Validate GitHub token format and basic structure"""
        if not token:
            return False
        return bool(re.match(r'^gh[ps]_[A-Za-z0-9_]{36,255}$', token))

    @staticmethod
    def validate_api_key(key: str, provider: str) -> bool:
        """Validate API key format for different providers"""
        patterns = {
            "openai": r'^sk-[A-Za-z0-9]{32,}$',
            "anthropic": r'^sk-ant-[A-Za-z0-9]{32,}$'
        }
        
        if provider not in patterns:
            return False
            
        return bool(re.match(patterns[provider], key))

    @staticmethod
    def validate_command(command: str) -> Tuple[bool, str]:
        """Validate command for basic security and syntax"""
        # List of dangerous commands/patterns
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"rm\s+-rf\s+~",
            r">\s+/dev/sd[a-z]",
            r"mkfs",
            r"dd\s+if=.+of=/dev/sd[a-z]"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command):
                return False, f"Potentially dangerous command pattern detected: {pattern}"
        
        return True, "Command validation passed"

class CacheHelper:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cached_data(self, key: str, max_age: timedelta = timedelta(hours=1)) -> Optional[Any]:
        """Get cached data if not expired"""
        cache_file = self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.json"
        
        if not cache_file.exists():
            return None
            
        data = json.loads(cache_file.read_text())
        cached_time = datetime.fromisoformat(data["timestamp"])
        
        if datetime.now() - cached_time > max_age:
            return None
            
        return data["value"]
    
    def set_cached_data(self, key: str, value: Any) -> None:
        """Cache data with timestamp"""
        cache_file = self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "value": value
        }
        
        cache_file.write_text(json.dumps(data))
    
    def clear_old_cache(self, max_age: timedelta = timedelta(days=7)) -> None:
        """Clear cache entries older than max_age"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text())
                cached_time = datetime.fromisoformat(data["timestamp"])
                
                if datetime.now() - cached_time > max_age:
                    cache_file.unlink()
            except Exception:
                # If there's any error reading/parsing the cache file, delete it
                cache_file.unlink()