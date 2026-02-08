import os
from pathlib import Path
from typing import Any, Dict

from symphony.tool import SymphonyTool

class SimpleFileSystemTool(SymphonyTool):
    """
    A tool for saving text content to a file.
    """
    def __init__(self, persona_name: str, user_id: str = "default"):
        self.persona_name = persona_name
        self.user_id = user_id
        self.base_path = Path("data/agents") / persona_name / "users" / user_id
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # --- Define the tool's properties for the LLM ---
        self.name = "save_text_to_file"
        # --- FIX: Made the description more assertive and purpose-driven ---
        self.description = "Your primary function is to save formatted content to a file. You MUST use this tool to complete any request involving writing, logging, or storing text."
        self.parameters = {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "The path of the file to save, relative to the user's directory, e.g., 'logs/daily.md'."
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write into the file."
                }
            },
            "required": ["relative_path", "content"]
        }

    def run(self, relative_path: str, content: str) -> Dict[str, Any]:
        """Saves the provided content to the specified file path."""
        try:
            file_path = self.base_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {"status": "success", "message": f"File saved to {file_path}", "full_path": str(file_path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# --- The Initialization Hook ---
def initialize_and_register(tool_registry, persona_name: str = None):
    """
    Initializes the tool and registers its *class* with the ToolRegistry.
    The Conductor will be responsible for instantiating it.
    """
    tool_registry.register("file_system_tool", SimpleFileSystemTool)