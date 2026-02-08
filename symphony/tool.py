from abc import ABC, abstractmethod
from typing import Any, Dict, List

class SymphonyTool(ABC):
    """
    A base class for all tools in the Symphony framework.
    
    This standardizes the tool API, making them easy to register and use
    with LLM function callers that support the OpenAI format.
    """
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Executes the tool's logic with the given arguments."""
        pass

    def to_openai_schema(self) -> Dict[str, Any]:
        """Converts the tool to the OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }