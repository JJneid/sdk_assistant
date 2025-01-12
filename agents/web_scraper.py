# agents/web_scraper.py
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
import json
import re
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import hashlib
import os

class WebScraperAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.cache_dir = os.path.join(os.getcwd(), 'cache')
        self.cache_duration = 3600  # 1 hour cache duration
        self.session = None
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Rate limiting settings
        self.rate_limits = {
            "pypi.org": {"calls": 0, "last_reset": time.time(), "limit": 30},  # 30 calls per minute
            "github.com": {"calls": 0, "last_reset": time.time(), "limit": 30},
            "readthedocs.org": {"calls": 0, "last_reset": time.time(), "limit": 30}
        }

    async def __aenter__(self):
        """Set up async context manager"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context manager"""
        if self.session:
            await self.session.close()

    async def gather_package_info(self, package_name: str) -> Dict[str, Any]:
        """
        Gather comprehensive information about a Python package.
        
        Args:
            package_name: Name of the Python package
            
        Returns:
            Dictionary containing package information from various sources
        """
        try:
            # Check cache first
            cache_key = f"package_info_{package_name}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

            # Gather information from multiple sources
            results = await asyncio.gather(
                self._fetch_pypi_info(package_name),
                self._fetch_github_info(package_name),
                self._fetch_readthedocs_info(package_name),
                self._fetch_package_docs(package_name)
            )

            package_info = {
                "pypi": results[0],
                "github": results[1],
                "readthedocs": results[2],
                "documentation": results[3],
                "last_updated": datetime.now().isoformat()
            }

            # Cache the results
            self._save_to_cache(cache_key, package_info)
            
            return package_info

        except Exception as e:
            self.logger.error(f"Error gathering package info for {package_name}: {str(e)}")
            raise

    async def _fetch_pypi_info(self, package_name: str) -> Dict[str, Any]:
        """Fetch package information from PyPI"""
        try:
            await self._check_rate_limit("pypi.org")
            
            url = f"https://pypi.org/pypi/{package_name}/json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract relevant information
                    info = data.get("info", {})
                    return {
                        "name": info.get("name"),
                        "version": info.get("version"),
                        "description": info.get("description"),
                        "author": info.get("author"),
                        "license": info.get("license"),
                        "project_urls": info.get("project_urls", {}),
                        "requires_dist": info.get("requires_dist", []),
                        "requires_python": info.get("requires_python"),
                        "summary": info.get("summary")
                    }
                return None

        except Exception as e:
            self.logger.error(f"Error fetching PyPI info for {package_name}: {str(e)}")
            return None

    async def _fetch_github_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch package information from GitHub"""
        try:
            await self._check_rate_limit("github.com")
            
            # Search for repository
            search_url = f"https://api.github.com/search/repositories?q={package_name}+language:python"
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            if os.getenv("GITHUB_TOKEN"):
                headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"

            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["items"]:
                        repo = data["items"][0]  # Get the most relevant repository
                        
                        # Fetch additional repo information
                        repo_url = repo["url"]
                        async with self.session.get(repo_url, headers=headers) as repo_response:
                            if repo_response.status == 200:
                                repo_data = await repo_response.json()
                                
                                return {
                                    "full_name": repo_data["full_name"],
                                    "description": repo_data["description"],
                                    "stars": repo_data["stargazers_count"],
                                    "forks": repo_data["forks_count"],
                                    "open_issues": repo_data["open_issues_count"],
                                    "last_update": repo_data["updated_at"],
                                    "license": repo_data.get("license", {}).get("name"),
                                    "topics": repo_data.get("topics", []),
                                    "homepage": repo_data.get("homepage"),
                                    "default_branch": repo_data["default_branch"]
                                }
                return None

        except Exception as e:
            self.logger.error(f"Error fetching GitHub info for {package_name}: {str(e)}")
            return None

    async def _fetch_readthedocs_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch documentation from Read the Docs"""
        try:
            await self._check_rate_limit("readthedocs.org")
            
            url = f"https://{package_name}.readthedocs.io/en/latest/"
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    return {
                        "url": url,
                        "title": soup.title.string if soup.title else None,
                        "sections": [
                            h.text for h in soup.find_all(['h1', 'h2', 'h3'])
                        ],
                        "last_updated": datetime.now().isoformat()
                    }
                return None

        except Exception as e:
            self.logger.error(f"Error fetching ReadTheDocs info for {package_name}: {str(e)}")
            return None

    async def _fetch_package_docs(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse package documentation"""
        try:
            # Try different documentation URLs
            doc_urls = [
                f"https://{package_name}.readthedocs.io/en/latest/",
                f"https://docs.{package_name}.org",
                f"https://{package_name}.org/docs"
            ]
            
            for url in doc_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract documentation content
                            content = {
                                "url": url,
                                "title": soup.title.string if soup.title else None,
                                "sections": {},
                                "examples": [],
                                "api_reference": {}
                            }
                            
                            # Extract main sections
                            for heading in soup.find_all(['h1', 'h2']):
                                section_id = heading.get('id', '')
                                section_content = []
                                
                                # Get all content until next heading
                                for elem in heading.next_siblings:
                                    if elem.name in ['h1', 'h2']:
                                        break
                                    if elem.name:
                                        section_content.append(elem.get_text())
                                
                                content["sections"][heading.text.strip()] = "\n".join(section_content)
                            
                            # Extract code examples
                            for code in soup.find_all('pre'):
                                if code.text.strip():
                                    content["examples"].append(code.text.strip())
                            
                            return content
                            
                except Exception as e:
                    self.logger.debug(f"Error fetching docs from {url}: {str(e)}")
                    continue
            
            return None

        except Exception as e:
            self.logger.error(f"Error fetching package docs for {package_name}: {str(e)}")
            return None

    async def _check_rate_limit(self, domain: str):
        """Check and enforce rate limits for different domains"""
        if domain in self.rate_limits:
            limit_info = self.rate_limits[domain]
            current_time = time.time()
            
            # Reset counter if minute has passed
            if current_time - limit_info["last_reset"] >= 60:
                limit_info["calls"] = 0
                limit_info["last_reset"] = current_time
            
            # Check if limit reached
            if limit_info["calls"] >= limit_info["limit"]:
                wait_time = 60 - (current_time - limit_info["last_reset"])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    limit_info["calls"] = 0
                    limit_info["last_reset"] = time.time()
            
            limit_info["calls"] += 1

    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.json")

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if it exists and is not expired"""
        cache_path = self._get_cache_path(key)
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached_data.get("cached_at", "2000-01-01"))
            if (datetime.now() - cached_time).total_seconds() < self.cache_duration:
                return cached_data.get("data")
        
        return None

    def _save_to_cache(self, key: str, data: Dict[str, Any]):
        """Save data to cache"""
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            "data": data,
            "cached_at": datetime.now().isoformat()
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)