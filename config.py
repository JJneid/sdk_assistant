# config.py
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG: Dict[str, Any] = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4-turbo-preview"
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model": "claude-3-opus-20240229"
    },
    "github": {
        "token": os.getenv("GITHUB_TOKEN"),
        "repo": os.getenv("GITHUB_REPO")
    }
}