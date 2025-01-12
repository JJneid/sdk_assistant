# agents/error_analyst.py
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import re
import json
import traceback
from bs4 import BeautifulSoup
import requests
import logging
from datetime import datetime

class ErrorAnalystAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.error_patterns = {
            "import": r"ImportError:|ModuleNotFoundError:",
            "syntax": r"SyntaxError:",
            "runtime": r"RuntimeError:",
            "attribute": r"AttributeError:",
            "type": r"TypeError:",
            "value": r"ValueError:",
            "key": r"KeyError:",
            "index": r"IndexError:",
            "permission": r"PermissionError:",
            "os": r"OSError:",
            "file": r"FileNotFoundError:"
        }
        
    async def analyze_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an error using AI models and web scraping for context.
        
        Args:
            error_data: Dictionary containing error information
                {
                    "error_message": str,
                    "traceback": str,
                    "command": str,
                    "context": Dict
                }
        """
        try:
            # Extract basic error information
            error_type = self._identify_error_type(error_data["error_message"])
            stack_analysis = self._analyze_traceback(error_data["traceback"])
            
            # Gather context from documentation
            docs_context = await self._gather_documentation(error_type, error_data["context"])
            
            # Prepare context for AI analysis
            analysis_context = {
                "error_message": error_data["error_message"],
                "error_type": error_type,
                "traceback": error_data["traceback"],
                "stack_analysis": stack_analysis,
                "command_context": error_data["command"],
                "documentation": docs_context
            }
            
            # Get AI analysis from both models
            analysis_prompt = self._load_prompt_template("error_analysis.txt")
            ai_analysis = await self.run_analysis(
                json.dumps(analysis_context),
                analysis_prompt
            )
            
            # Combine all information
            complete_analysis = {
                "error_type": error_type,
                "stack_trace": stack_analysis,
                "ai_analysis": ai_analysis,
                "documentation_refs": docs_context,
                "solutions": await self._generate_solutions(ai_analysis, docs_context),
                "prevention_tips": await self._generate_prevention_tips(ai_analysis),
                "similar_errors": await self._find_similar_errors(error_type, error_data["error_message"])
            }
            
            return complete_analysis
            
        except Exception as e:
            self.logger.error(f"Error during error analysis: {str(e)}")
            raise

    def _identify_error_type(self, error_message: str) -> str:
        """Identify the type of error from the error message"""
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, error_message):
                return error_type
        return "unknown"

    def _analyze_traceback(self, traceback_str: str) -> Dict[str, Any]:
        """Analyze the traceback to extract useful information"""
        analysis = {
            "frames": [],
            "files_involved": set(),
            "line_numbers": [],
            "local_vars": {}
        }
        
        try:
            # Parse traceback string
            for line in traceback_str.split('\n'):
                if "File" in line:
                    # Extract filename and line number
                    match = re.search(r'File "([^"]+)", line (\d+)', line)
                    if match:
                        filename, line_num = match.groups()
                        analysis["files_involved"].add(filename)
                        analysis["line_numbers"].append(int(line_num))
                        
                        frame = {
                            "file": filename,
                            "line": int(line_num),
                            "context": line.strip()
                        }
                        analysis["frames"].append(frame)
                
                # Look for local variables in traceback
                if "locals" in line:
                    vars_match = re.findall(r'(\w+)\s*=\s*([^,]+)', line)
                    for var_name, var_value in vars_match:
                        analysis["local_vars"][var_name] = var_value.strip()
            
            return analysis
            
        except Exception as e:
            self.logger.warning(f"Error analyzing traceback: {str(e)}")
            return analysis

    async def _gather_documentation(self, error_type: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Gather relevant documentation for the error type"""
        docs = {}
        
        try:
            # Python official documentation
            python_docs = await self._scrape_python_docs(error_type)
            if python_docs:
                docs["python_official"] = python_docs
            
            # Package-specific documentation if available
            if "packages" in context:
                for package in context["packages"]:
                    package_docs = await self._scrape_package_docs(package, error_type)
                    if package_docs:
                        docs[f"{package}_docs"] = package_docs
            
            # Stack Overflow relevant posts
            stackoverflow_refs = await self._fetch_stackoverflow_refs(error_type)
            if stackoverflow_refs:
                docs["stackoverflow_refs"] = stackoverflow_refs
            
            return docs
            
        except Exception as e:
            self.logger.warning(f"Error gathering documentation: {str(e)}")
            return docs

    async def _scrape_python_docs(self, error_type: str) -> Optional[str]:
        """Scrape Python documentation for error type"""
        try:
            url = f"https://docs.python.org/3/library/exceptions.html#{error_type.lower()}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                error_section = soup.find('dt', {'id': error_type.lower()})
                if error_section:
                    return error_section.find_next('dd').get_text()
            return None
        except Exception:
            return None

    async def _generate_solutions(self, ai_analysis: Dict[str, Any], docs_context: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate potential solutions based on AI analysis and documentation"""
        solutions = []
        
        # Extract solutions from AI analysis
        if "solutions" in ai_analysis:
            for solution in ai_analysis["solutions"]:
                solutions.append({
                    "description": solution,
                    "confidence": "high",
                    "source": "ai_analysis"
                })
        
        # Extract solutions from documentation
        for source, content in docs_context.items():
            if "solution" in content.lower() or "fix" in content.lower():
                solutions.append({
                    "description": content,
                    "confidence": "medium",
                    "source": source
                })
        
        return solutions

    async def _generate_prevention_tips(self, ai_analysis: Dict[str, Any]) -> List[str]:
        """Generate tips to prevent similar errors in the future"""
        prevention_tips = set()
        
        if "prevention" in ai_analysis:
            prevention_tips.update(ai_analysis["prevention"])
        
        # Add general best practices based on error type
        if "error_type" in ai_analysis:
            best_practices = await self._fetch_best_practices(ai_analysis["error_type"])
            prevention_tips.update(best_practices)
        
        return list(prevention_tips)

    async def _find_similar_errors(self, error_type: str, error_message: str) -> List[Dict[str, Any]]:
        """Find similar errors from various sources"""
        similar_errors = []
        
        try:
            # Search GitHub issues
            github_issues = await self.user_proxy.initiate_chat(
                self.assistant,
                message=f"Search for GitHub issues related to: {error_type} {error_message}"
            )
            
            # Search Stack Overflow
            stackoverflow_results = await self._fetch_stackoverflow_refs(error_type)
            
            # Combine and deduplicate results
            if github_issues:
                similar_errors.extend(github_issues)
            if stackoverflow_results:
                similar_errors.extend(stackoverflow_results)
            
            return similar_errors[:5]  # Return top 5 most relevant
            
        except Exception as e:
            self.logger.warning(f"Error finding similar errors: {str(e)}")
            return []

    async def _fetch_best_practices(self, error_type: str) -> List[str]:
        """Fetch best practices for preventing specific types of errors"""
        practices = set()
        
        # Use AI to generate best practices
        prompt = f"What are the best practices to prevent {error_type} errors in Python?"
        
        try:
            response = await self.run_analysis(prompt, "best_practices_template.txt")
            if isinstance(response, dict) and "practices" in response:
                practices.update(response["practices"])
            
            return list(practices)
            
        except Exception as e:
            self.logger.warning(f"Error fetching best practices: {str(e)}")
            return list(practices)