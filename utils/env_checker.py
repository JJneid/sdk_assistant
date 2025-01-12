# sdk_assistant/utils/env_checker.py
import os
from typing import List, Dict
from rich.console import Console
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

console = Console()

def debug_env_loading():
    """Debug environment variable loading"""
    # Find .env file
    env_path = find_dotenv()
    console.print(f"\nEnvironment Setup Debug:")
    console.print(f"------------------------")
    console.print(f"Current working directory: {os.getcwd()}")
    console.print(f".env file path: {env_path}")
    
    if env_path:
        console.print(f"[green].env file found at: {env_path}[/green]")
        # Load the environment variables
        load_dotenv(env_path)
    else:
        console.print("[red].env file not found![/red]")
        return False
    
    # Check file contents (safely)
    try:
        with open(env_path) as f:
            lines = f.readlines()
            console.print("\nEnvironment variables found:")
            for line in lines:
                if '=' in line:
                    key = line.split('=')[0].strip()
                    console.print(f"- {key}: {'✓' if os.getenv(key) else '✗'}")
    except Exception as e:
        console.print(f"[red]Error reading .env file: {str(e)}[/red]")
        return False
    
    return True

def check_environment() -> Dict[str, bool]:
    """Check if all required environment variables are set."""
    # Try to load environment variables
    debug_env_loading()
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for AI functionality",
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude integration",
        "GITHUB_TOKEN": "GitHub token for issue management",
        "GITHUB_REPO": "GitHub repository for issue tracking"
    }
    
    status = {}
    
    console.print("\nChecking Required Variables:")
    console.print("---------------------------")
    for var, description in required_vars.items():
        value = os.getenv(var)
        status[var] = bool(value)
        if not value:
            console.print(f"[red]Warning: {var} not found - {description}[/red]")
        else:
            console.print(f"[green]✓ {var} configured[/green]")
    
    return status