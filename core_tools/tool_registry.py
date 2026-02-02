class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, func):
        """Register a tool function in the registry.
        
        Args:
            func: A callable function with a descriptive docstring
        """
        if not callable(func):
            raise ValueError("Tool must be callable")
        
        if not func.__doc__:
            raise ValueError(f"Tool {func.__name__} must have a docstring")
        
        tool_name = func.__name__
        self.tools[tool_name] = {
            'function': func,
            'name': tool_name,
            'description': func.__doc__.strip()
        }
    
    def get_tools_for_prompt(self):
        """Format all registered tools into a string for the AI prompt.
        
        Returns:
            str: Formatted list of available tools
        """
        if not self.tools:
            return "No tools available."
        
        tool_list = []
        for tool_name, tool_info in self.tools.items():
            func = tool_info['function']
            # Get function signature for argument display
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            if params:
                tool_list.append(f"- {tool_name}({', '.join(params)}): {tool_info['description']}")
            else:
                tool_list.append(f"- {tool_name}(): {tool_info['description']}")
        
        return "\n".join(tool_list)
    
    def get_tool(self, name):
        """Get a tool function by name.
        
        Args:
            name (str): Name of the tool to retrieve
            
        Returns:
            callable: The tool function
            
        Raises:
            ValueError: If tool is not found
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found. Available tools: {list(self.tools.keys())}")
        
        return self.tools[name]['function']
    
    def call_tool(self, name, **kwargs):
        """Call a tool by name with provided arguments.
        
        Args:
            name (str): Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result of the tool function call
            
        Raises:
            ValueError: If tool is not found or call fails
        """
        try:
            tool_func = self.get_tool(name)
            return tool_func(**kwargs)
        except Exception as e:
            raise ValueError(f"Error calling tool '{name}': {str(e)}")