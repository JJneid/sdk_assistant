# agents/base_agent.py
from typing import Optional, Dict, Any
import autogen
from ..ai.openai_client import OpenAIClient
from ..ai.claude_client import ClaudeClient

class BaseAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_client = OpenAIClient(config["openai"])
        self.claude_client = ClaudeClient(config["anthropic"])
        
        # Initialize autogen agents
        self.assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config={
                "config_list": [
                    {
                        "model": config["openai"]["model"],
                        "api_key": config["openai"]["api_key"]
                    }
                ]
            }
        )
        
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10
        )

    async def run_analysis(self, content: str, prompt_template: str) -> Dict[str, Any]:
        """Run analysis using both OpenAI and Claude, combine results"""
        openai_response = await self.openai_client.analyze(content, prompt_template)
        claude_response = await self.claude_client.analyze(content, prompt_template)
        
        # Combine insights from both models
        combined_analysis = self._merge_analyses(openai_response, claude_response)
        return combined_analysis

    def _merge_analyses(self, openai_analysis: Dict, claude_analysis: Dict) -> Dict:
        """Merge analyses from different models, keeping unique insights"""
        # Implementation depends on the specific analysis structure
        pass
