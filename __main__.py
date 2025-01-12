# sdk_assistant/__main__.py
import typer
import asyncio
from rich.console import Console
from rich import print
import sys
from pathlib import Path
from typing import Optional

from sdk_assistant import SDKAssistant
from sdk_assistant.utils.logger import setup_logger


# At the top of __main__.py
try:
    import openai
    print(f"OpenAI version: {openai.__version__}")
except ImportError as e:
    print(f"Error importing OpenAI: {e}")

try:
    from openai import OpenAI
    print("OpenAI client imported successfully")
except ImportError as e:
    print(f"Error importing OpenAI client: {e}")

    
app = typer.Typer()
console = Console()
logger = setup_logger()

async def run_assistant(description: str):
    """Run the SDK Assistant with the given description."""
    try:
        # Initialize with config
        assistant = SDKAssistant({
            "openai": {
                "model": "gpt-4-turbo-preview"
            },
            "anthropic": {
                "model": "claude-3-opus-20240229"
            }
        })
        
        await assistant.start_session(description)
        
        try:
            while True:
                command = typer.prompt("Enter command (or 'exit' to finish)")
                
                if command.lower() == 'exit':
                    break
                    
                try:
                    result = await assistant.execute_command(command)
                    if result.get("exit_code") == 0:
                        console.print("[green]Command executed successfully[/green]")
                    else:
                        console.print("[red]Command failed[/red]")
                        console.print(f"Error: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    console.print(f"[red]Error executing command: {str(e)}[/red]")
        
        finally:
            # Generate tutorial before closing
            try:
                tutorial = await assistant.generate_tutorial()
                console.print(f"\n[green]Tutorial generated: {tutorial.get('path', 'tutorial.md')}[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not generate tutorial: {str(e)}[/yellow]")
            
            # Close session
            await assistant.close_session()
            
    except Exception as e:
        console.print(f"[red]Error initializing assistant: {str(e)}[/red]")
        raise

@app.command()
def start(description: str = typer.Option(..., help="Description of what you're trying to do")):
    """Start the SDK Assistant."""
    try:
        # Check environment first
        from sdk_assistant.utils.env_checker import check_environment
        env_status = check_environment()
        
        if not all(env_status.values()):
            console.print("\n[red]Error: Missing required environment variables[/red]")
            sys.exit(1)
            
        asyncio.run(run_assistant(description))
    except KeyboardInterrupt:
        console.print("\n[yellow]Session terminated by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

@app.command()
def version():
    """Show version information."""
    from sdk_assistant import __version__
    console.print(f"SDK Assistant version {__version__}")

if __name__ == "__main__":
    app()