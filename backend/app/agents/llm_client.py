from typing import Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)

class LocalLLMClient:
    """Client for local LLM (Ollama, LM Studio, etc.)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using local LLM"""
        try:
            # Example for Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                }
            )
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return ""
    
    async def generate_ddl(self, mysql_schema: dict) -> str:
        """Use LLM to generate Snowflake DDL"""
        prompt = f"""
You are a data engineer. Convert this MySQL schema to Snowflake DDL.

MySQL Schema:
{mysql_schema}

Generate a CREATE TABLE statement for Snowflake.
Use appropriate Snowflake data types.
Add comments where necessary.

Snowflake DDL:
"""
        return await self.generate(prompt)