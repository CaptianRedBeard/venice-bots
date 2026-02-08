from typing import Dict, Any, Type, List

class ToolRegistry:
    """ A simple registry for tool classes. """
    def __init__(self):
        self._tools: Dict[str, Type] = {}

    def register(self, tool_name: str, tool_class: Type):
        """Registers a tool class by name."""
        if tool_name in self._tools:
            print(f"Warning: Tool '{tool_name}' is being overwritten.")
        self._tools[tool_name] = tool_class
        print(f"✓ Registered tool: {tool_name}")

    def get(self, tool_name: str) -> Type:
        """Retrieves a tool class by name."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        return self._tools[tool_name]

    def list_tools(self) -> List[str]:
        """Returns a list of all registered tool names."""
        return list(self._tools.keys())