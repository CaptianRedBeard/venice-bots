import json
from typing import Dict, Any, Tuple, List
from .config import get_venice_client, get_model_for_role
from .exceptions import ToolError

class LLMFunctionCaller:
    """ A stateless parser that uses an LLM to determine user intent and extract arguments. It dynamically uses a list of tool schemas and optional headers provided at runtime. """

    def __init__(self, role: str = "function_calling"):
        """ Initializes the LLMFunctionCaller. Args: role (str): The model role to use (e.g., 'function_calling'). """
        self.client = get_venice_client()
        self.model = get_model_for_role(role)

    def parse(self, user_input: str, schemas: list, available_headers: list = None, is_reparse: bool = False) -> tuple:
        """Parses user input to select a function and its arguments."""
        prompt = f"""You are an expert at parsing user requests to select the correct function and its arguments. Based on the user's input and the available function schemas, determine the best function to call.
        
        Available Functions:
        {json.dumps(schemas, indent=2)}
        """
        
        # This single block now handles all dynamic logic
        if available_headers:
            headers_string = "\n".join(available_headers)
            prompt += f"""
            
            DYNAMIC INSTRUCTION FOR 'append_to_section':
            - The user wants to add text to a section.
            - You MUST choose the most appropriate 'section_header' from the following list of all available headers in the target journal file.
            - Avoid top-level titles (e.g., '# Daily Log') and choose a more specific section (e.g., '## Mood', '### Project X').
            --- Available Headers ---
            {headers_string}
            -------------------------
            - Do not invent a header. Use one from the list above.
            
            INSTRUCTION FOR 'file_type' and 'target_date':
            - If the user mentions 'weekly' or 'week', set 'file_type' to 'weekly'. Otherwise, assume 'daily'.
            - If the user mentions a specific date (e.g., 'yesterday', 'for 2026-02-10'), include it in the 'target_date' argument.
            """
        
        prompt += f"""
        
        User Input: "{user_input}"

        Based on the user input and the available headers above, determine the correct function and its arguments.
        Respond ONLY with a JSON object containing two keys: "function_name" and "arguments".
        - The 'file_path' argument for 'append_to_section' will be handled by the system.
        - If no function matches the input, respond with {{"function_name": "unknown", "arguments": {{}}}}.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            raw_response = response.choices[0].message.content.strip()
            
            # Clean up potential markdown formatting
            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "").strip()
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3].strip()

            parsed_response = json.loads(raw_response)
            function_name = parsed_response.get("function_name")
            arguments = parsed_response.get("arguments", {})

            if not isinstance(function_name, str) or not isinstance(arguments, dict):
                raise ValueError("LLM response is not in the expected format.")
                
            return function_name, arguments

        except json.JSONDecodeError as e:
            print(f"Error decoding LLM response: {e}")
            print(f"Raw response was: {raw_response}")
            return "unknown", {}
        except Exception as e:
            print(f"An error occurred during LLM call: {e}")
            return "unknown", {}
        
        