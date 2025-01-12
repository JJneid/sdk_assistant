# agents/doc_generator.py
from .base_agent import BaseAgent
from typing import Dict, Any, List
import markdown2

class DocGeneratorAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    async def generate_tutorial(self, session_data: Dict[str, Any]) -> str:
        # Load tutorial generation prompt
        prompt = self._load_prompt_template("tutorial_generation.txt")
        
        # Prepare context for AI analysis
        context = {
            "description": session_data["description"],
            "commands": session_data["commands"],
            "errors": session_data["errors"],
            "context": session_data["context"]
        }
        
        # Generate tutorial using both AI models
        tutorial_content = await self.run_analysis(
            str(context),
            prompt
        )
        
        # Convert to markdown
        markdown = self._format_tutorial(tutorial_content)
        return markdown

    def _format_tutorial(self, content: Dict[str, Any]) -> str:
        """Format the AI-generated content into a proper markdown tutorial"""
        sections = [
            "# Tutorial: {title}",
            "\n## Overview",
            "{overview}",
            "\n## Prerequisites",
            "{prerequisites}",
            "\n## Steps",
            "{steps}",
            "\n## Common Issues and Solutions",
            "{issues}",
            "\n## Additional Resources",
            "{resources}"
        ]
        
        return "\n".join(sections).format(**content)