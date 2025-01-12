# ai/claude_client.py
from anthropic import Anthropic
from typing import Dict, Any

class ClaudeClient:
    def __init__(self, config: Dict[str, Any]):
        self.client = Anthropic(api_key=config["api_key"])
        self.model = config["model"]

    async def analyze(self, content: str, prompt_template: str) -> Dict[str, Any]:
        prompt = prompt_template.format(content=content)
        
        response = await self.client.messages.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n{content}"
                }
            ]
        )
        
        return response.content[0].text