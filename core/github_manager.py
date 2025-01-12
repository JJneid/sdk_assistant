# core/github_manager.py
from github import Github
from typing import Dict, List, Optional, Union
import os
from dotenv import load_dotenv
from pathlib import Path

class GitHubManager:
    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """
        Initialize GitHub manager with token and repository name.
        
        Args:
            token: GitHub access token. If None, tries to get from environment
            repo_name: Repository name in format "owner/repo". If None, tries to get from environment
        """
        # Load environment variables from .env file
        env_path = Path('.env')
        load_dotenv(dotenv_path=env_path)
        
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN not found in environment. "
                           "Please add GITHUB_TOKEN to your .env file or provide it directly.")
            
        self.repo_name = repo_name or os.getenv("GITHUB_REPO")
        if not self.repo_name:
            raise ValueError("Repository name not provided and GITHUB_REPO not found in environment. "
                           "Please add GITHUB_REPO to your .env file or provide it directly.")
            
        try:
            self.github = Github(self.token)
            self.repo = self.github.get_repo(self.repo_name)
        except Exception as e:
            raise ValueError(f"Failed to initialize GitHub client: {str(e)}")