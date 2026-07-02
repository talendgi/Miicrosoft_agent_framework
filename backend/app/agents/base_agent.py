from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all LLM agents"""
    
    def __init__(self, model: str = "local"):
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input and return output"""
        pass
    
    def log(self, message: str, level: str = "info"):
        """Helper for consistent logging"""
        log_func = getattr(self.logger, level)
        log_func(f"[{self.__class__.__name__}] {message}")