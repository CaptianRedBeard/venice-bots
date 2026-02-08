import json
from typing import Any, Dict, Tuple # <-- ADDED Tuple HERE

from .config import get_venice_client, get_model_for_role
from .exceptions import ToolError

class SymphonyFunctionCaller:
    """
    An intelligent function caller that integrates with the ToolRegistry.
    It dynamically loads tool schemas, parses user input, and executes the function.
    """
    def __init__(self, tool_registry, role: str = "function_calling"):
        """
        Initializes the SymphonyFunctionCaller.
        Args:
            tool_registry: An instance of the shared ToolRegistry.
            role (str): The model role to use (e.g., 'function_calling').
        """
        self.client = get_venice_client()
        self.model = get_model_for_role(role)
        self.tool_registry = tool_registry

    def _get_all_schemas(self) -> list:
        """Collects all function schemas from the ToolRegistry."""
        return self.tool_registry.get_all_schemas()

    def parse_and_execute(self, user_input: str, persona_name: str) -> Tuple[str, Any]:
        """
        Parses user input to select a function, its arguments, and executes it.
        
        Args:
            user_input (str): The raw input from the user.
            persona_name (str): The name of the persona. (No longer needed for execution, but kept for consistency)

        Returns:
            Tuple[str, Any]: A tuple containing the function name and the result of the execution.
        """
        schemas = self._get_all_schemas()
        
        # --- DEBUG: Print the schemas being sent to the LLM ---
        print("--- DEBUG: Schemas being sent to LLM ---")
        print(json.dumps(schemas, indent=2))
        print("--- END DEBUG ---")
        
        prompt = f"""You are an expert at parsing user requests to select the correct function and its arguments. Based on the user's input and the available function schemas, determine the best function to call.

Available Functions:
{json.dumps(schemas, indent=2)}

User Input: "{user_input}"

Based on the user input, determine the correct function and its arguments. Respond ONLY with a JSON object containing two keys: "function_name" and "arguments".
- The "function_name" must be one of the "name" values from the "Available Functions" list above.
- If no function matches the input, respond with {{"function_name": "unknown", "arguments": {{}}}}.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            raw_response = response.choices[0].message.content.strip()
            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "").strip()
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3].strip()
            
            parsed_response = json.loads(raw_response)
            function_name = parsed_response.get("function_name")
            arguments = parsed_response.get("arguments", {})

            if function_name == "unknown":
                return "unknown", "I'm not sure how to handle that request."

            # --- Execute the function using the ToolRegistry's call method ---
            result = self.tool_registry.call(function_name, **arguments)
            return function_name, result

        except Exception as e:
            print(f"An error occurred during function call: {e}")
            return "error", str(e)
