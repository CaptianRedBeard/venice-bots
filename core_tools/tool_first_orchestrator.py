import re
import json
from .intent_classifier import IntentClassifier
from .tool_registry import ToolRegistry
from .config import get_venice_client

class ToolFirstOrchestrator:
    """
    An orchestrator that implements a "Tool Execution -> LLM Synthesis" workflow.
    This is designed to be more reliable than LLM-based planning.
    """
    def __init__(self, tool_registry: ToolRegistry, llm_client):
        """
        Initializes the ToolFirstOrchestrator.
        
        Args:
            tool_registry (ToolRegistry): An instance of the tool registry.
            llm_client: An instance of the Venice LLM client.
        """
        if not isinstance(tool_registry, ToolRegistry):
            raise TypeError("tool_registry must be an instance of ToolRegistry.")
        self.tool_registry = tool_registry
        self.llm_client = llm_client
        self.classifier = IntentClassifier()

    def _execute_tool(self, tool_name: str, user_input: str):
        """
        Executes a tool with sensible defaults based on the user input.
        
        Args:
            tool_name (str): The name of the tool to execute.
            user_input (str): The original user input to parse for arguments.
            
        Returns:
            The raw result from the tool, or an error string.
        """
        try:
            if tool_name == "find_files":
                # Try to find a quoted pattern first
                pattern_match = re.search(r"['\"]([^'\"]+)['\"]", user_input)
                if pattern_match:
                    pattern = pattern_match.group(1)
                else:
                    # Fallback: find the word after "find" or "named"
                    match = re.search(r"(?:find|named)\s+(\S+)", user_input, re.IGNORECASE)
                    pattern = match.group(1) if match else "*"
                return self.tool_registry.call_tool("find_files", pattern=pattern, root_path=".")
            
            elif tool_name == "read_file":
                # Try to find a quoted path first
                path_match = re.search(r"['\"]([^'\"]+)['\"]", user_input)
                if path_match:
                    path = path_match.group(1)
                else:
                    # Fallback: find the word after "read" or "file"
                    match = re.search(r"(?:read|file)\s+(\S+)", user_input, re.IGNORECASE)
                    if match:
                        path = match.group(1)
                    else:
                        return "Error: Please specify a file path."
                
                return self.tool_registry.call_tool("read_file", path=path)

            elif tool_name == "list_directory":
                # Try to find a quoted path first
                path_match = re.search(r"['\"]([^'\"]+)['\"]", user_input)
                if path_match:
                    path = path_match.group(1)
                else:
                    # Fallback: find the word after "in"
                    match = re.search(r"in\s+(\S+)", user_input, re.IGNORECASE)
                    path = match.group(1) if match else "."
                
                return self.tool_registry.call_tool("list_directory", path=path)
            
            else:
                return f"Error: Unknown tool '{tool_name}' selected for execution."

        except Exception as e:
            return f"Error during tool execution: {e}"

    def _synthesize_response(self, tool_output: any, persona_config: dict) -> str:
        """
        Uses an LLM to synthesize the raw tool output into a user-friendly response.
        
        Args:
            tool_output (any): The raw output from the executed tool.
            persona_config (dict): The persona configuration to use for the response.
            
        Returns:
            A formatted, user-friendly string from the LLM.
        """
        system_prompt = persona_config.get('system_prompt', "You are a helpful assistant.")
        
        # A simple, direct prompt for synthesis
        synthesis_prompt = f"""You are a helpful assistant. Your task is to summarize the following data for the user based on your persona. Do not add information that is not present in the data. If the data is an error message, report the error clearly and concisely.

Data:
{json.dumps(tool_output, indent=2)}

Summary:"""
        
        try:
            # Use the model specified in the persona config, with a fallback
            model = persona_config.get('models', {}).get('synthesis', 'llama-3.2-3b')
            response = self.llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to a non-LLM response if LLM synthesis fails
            return f"I was able to execute the tool, but I had trouble formatting the response. Here is the raw data:\n{tool_output}"

    def run(self, user_input: str, persona_config: dict) -> str:
        """
        Runs the full "Tool-First" workflow: Classify, Execute, Synthesize.
        
        Args:
            user_input (str): The input string from the user.
            persona_config (dict): The configuration for the agent's persona.
            
        Returns:
            The final, synthesized response for the user.
        """
        # 1. Classify
        tool_name = self.classifier.classify(user_input)
        
        if tool_name == "unknown":
            persona_desc = persona_config.get('description', 'a helpful assistant')
            return f"I'm not sure how to handle that request. I am {persona_desc} and can help you find files, read file contents, or list directories."

        # 2. Execute
        tool_output = self._execute_tool(tool_name, user_input)

        # 3. Synthesize
        final_response = self._synthesize_response(tool_output, persona_config)
        
        return final_response