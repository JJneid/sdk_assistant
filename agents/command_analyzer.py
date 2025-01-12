# agents/command_analyzer.py
from typing import Dict, Any
from .base_agent import BaseAgent
import re
from bs4 import BeautifulSoup
import requests

class CommandAnalyzerAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.command_context = {}

    async def analyze_command(self, command: str, output: str) -> Dict[str, Any]:
        # Extract package names and documentation
        packages = self._extract_packages(command)
        docs = await self._fetch_package_docs(packages)
        
        # Use AI to analyze command purpose and context
        analysis_prompt = self._load_prompt_template("command_analysis.txt")
        analysis = await self.run_analysis(
            f"Command: {command}\nOutput: {output}\nPackages: {docs}",
            analysis_prompt
        )
        
        return {
            "command": command,
            "packages": packages,
            "documentation": docs,
            "analysis": analysis
        }

    async def _fetch_package_docs(self, packages: list) -> Dict[str, str]:
        docs = {}
        for package in packages:
            # Use autogen for web scraping
            scraping_task = f"Fetch documentation for Python package {package}"
            chat = await self.user_proxy.initiate_chat(
                self.assistant,
                message=scraping_task
            )
            
            # Parse PyPI and ReadTheDocs
            pypi_info = await self._scrape_pypi(package)
            readthedocs = await self._scrape_readthedocs(package)
            
            docs[package] = {
                "pypi": pypi_info,
                "readthedocs": readthedocs
            }
        
        return docs

    async def _scrape_pypi(self, package: str) -> Dict[str, Any]:
        url = f"https://pypi.org/project/{package}/"
        
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return {
                "description": soup.find("div", {"class": "project-description"}).text,
                "version": soup.find("h1", {"class": "package-header__name"}).text,
                "url": url
            }
        except Exception as e:
            return {"error": str(e)}