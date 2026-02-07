import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable, List

class ToolRegistry:
    """
    A central registry for all tools available to agents.
    This version supports self-describing tools with schemas, init hooks,
    and manages both standalone functions and methods on class instances.
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(self, tool_name: str, tool_callable: Callable, schema: Dict[str, Any] = None, init_hook: Callable = None):
        """
        Registers a tool with a given name, its callable, an optional schema, and an optional init hook.
        
        Args:
            tool_name (str): The unique name for the tool.
            tool_callable (Callable): The function or method to call.
            schema (Dict[str, Any]): A JSON schema describing the tool's arguments.
            init_hook (Callable): An optional function to run before the main tool to prepare arguments.
        """
        if tool_name in self.tools:
            print(f"Warning: Tool '{tool_name}' is being overwritten.")
        
        self.tools[tool_name] = {
            "callable": tool_callable,
            "schema": schema or {},
            "init_hook": init_hook
        }
        print(f"✓ Registered tool: {tool_name}")

    def get(self, tool_name: str) -> Callable:
        """Retrieves a tool's callable by name."""
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        return tool_info["callable"]

    def get_schema(self, tool_name: str) -> Dict[str, Any]:
        """Retrieves a tool's schema by name."""
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        return tool_info["schema"]

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all registered tool schemas, formatted for LLM consumption.
        Each schema is a dictionary containing the tool's name and its parameters.
        """
        formatted_schemas = []
        for name, info in self.tools.items():
            if info["schema"]: # Only include tools that have a schema
                formatted_schemas.append({
                    "name": name,
                    "description": info["schema"].get("description", "No description available."),
                    "parameters": info["schema"].get("parameters", {})
                })
        return formatted_schemas

    def call(self, tool_name: str, **kwargs) -> Any:
        """
        Executes a tool by name with the given arguments.
        Runs an init_hook first if one is registered.
        """
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

        # Run the init_hook if it exists to prepare/modify the arguments
        init_hook = tool_info.get("init_hook")
        if init_hook:
            kwargs = init_hook(**kwargs)

        tool_callable = tool_info["callable"]
        try:
            return tool_callable(**kwargs)
        except TypeError as e:
            raise ValueError(f"Error calling tool '{tool_name}': {e}")

    def list_tools(self) -> List[str]:
        """Returns a list of all registered tool names."""
        return list(self.tools.keys())