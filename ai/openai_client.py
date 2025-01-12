# ai/openai_client.py
from openai import OpenAI
from typing import Dict, Any
import os
from dotenv import load_dotenv

class OpenAIClient:
    def __init__(self, config: Dict[str, Any]):
        load_dotenv()
        
        self.client = OpenAI(
            api_key=config.get("api_key") or os.getenv("OPENAI_API_KEY"),
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            max_retries=config.get("max_retries", 2),
            timeout=config.get("timeout", 600)  # 10 minutes
        )
        self.model = config.get("model", "gpt-4-turbo-preview")

    async def analyze(self, content: str, prompt_template: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=False
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return {"error": f"OpenAI API error: {str(e)}"}

    async def stream_analysis(self, content: str, prompt_template: str):
        """Stream the response from OpenAI"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error: {str(e)}"

    async def generate_tutorial(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation with streaming support"""
        template = """Generate a detailed tutorial based on the session data.
        Include steps, code examples, and error handling."""
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": template},
                    {"role": "user", "content": str(session_data)}
                ],
                temperature=0.7,
                stream=True
            )
            
            tutorial_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    tutorial_content += chunk.choices[0].delta.content
            
            return {"content": tutorial_content}
            
        except Exception as e:
            return {"error": f"Error generating tutorial: {str(e)}"}