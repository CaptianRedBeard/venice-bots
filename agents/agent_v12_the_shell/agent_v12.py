import sys
import os
import json
import logging
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# --- Core Framework Imports ---
from symphony.config import get_venice_client, get_model_for_role

class StructuredJSONFormatter(logging.Formatter):
    """A custom formatter to output logs as a single line of JSON."""
    def format(self, record):
        # Ensure 'details' key exists
        if not hasattr(record, 'details'):
            record.details = {}
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "agent": record.name,
            "event": record.msg, # Use the log message as the event name
            "details": record.details
        }
        return json.dumps(log_entry)

class AgentShell:
    """
    A robust, dynamically configurable agent shell designed for the Symphony framework.
    This agent is a "doer" that receives a dictionary of instantiated tool objects
    and a persona configuration from a Conductor and uses them to perform tasks.
    """
    def __init__(
        self,
        persona_name: str,
        persona_config: Dict[str, Any],
        instantiated_tools: Optional[Dict[str, Any]] = None
    ):
        """
        Initializes the Agent V12 Shell.

        Args:
            persona_name (str): The name of the persona.
            persona_config (Dict[str, Any]): The persona's configuration dictionary.
            instantiated_tools (Optional[Dict[str, Any]]): A dictionary of pre-instantiated tool objects.
        """
        # 1. Store Persona Configuration directly
        self.persona_name = persona_name
        self.persona_config = persona_config
        self._setup_logging()
        
        # 2. Initialize Core Components
        self.llm_client = get_venice_client()

        # 3. Store tools using their function name for easy lookup
        self.tools = {}
        if instantiated_tools:
            for tool in instantiated_tools.values():
                self.tools[tool.name] = tool

        self.logger.info("agent_initialized", extra={
            "details": {
                "persona": persona_name,
                "provided_tools": list(self.tools.keys())
            }
        })

        self.logger.info("agent_setup_complete", extra={
            "details": {
                "final_toolset": list(self.tools.keys())
            }
        })

    def _setup_logging(self):
        """
        Configures the agent's logger to write to a file by default.
        This prevents cluttering the terminal during normal operation.
        """
        self.logger = logging.getLogger(self.persona_config.get('name', 'AgentShell'))
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers to ensure a clean state
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create a logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create a file handler instead of a stream handler
        log_file_path = logs_dir / f"{self.persona_name}.log"
        file_handler = logging.FileHandler(log_file_path, 'w', encoding='utf-8')
        file_handler.setFormatter(StructuredJSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Prevent logs from propagating to the root logger (and thus the console)
        self.logger.propagate = False

    def _synthesize_response(self, tool_output: Any) -> str:
        """Uses an LLM to synthesize the raw tool output into a user-friendly response."""
        system_prompt = self.persona_config.get('system_prompt', "You are a helpful assistant.")
        synthesis_prompt = f"""Summarize the following data for the user based on your persona. Do not add information that is not present in the data. If the data is an error message, report it clearly. Data: {json.dumps(tool_output, indent=2)} Summary:"""
        try:
            model = get_model_for_role('synthesis')
            response = self.llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": synthesis_prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error("response_synthesis_failed", extra={
                "details": {"error": str(e), "raw_output": str(tool_output)}
            })
            return f"I was able to execute a tool, but I had trouble formatting the response. Here is the raw data:\n{tool_output}"

    def _get_fallback_response(self) -> str:
        """Provides a graceful response when the agent has no configured tools."""
        return "I am the default agent and have not been configured with any tools. How can I help?"

    def _call_llm_with_functions(self, user_input: str, openai_schemas: List[Dict[str, Any]]) -> tuple:
        """
        Performs a standard OpenAI function-calling API call.
        This is a generic helper that can be used by any agent.
        """
        model = get_model_for_role('function_calling')
        try:
            response = self.llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_input}],
                tools=openai_schemas,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                tool_call = tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                return function_name, function_args
            else:
                return "unknown", {}

        except Exception as e:
            self.logger.error("llm_function_call_failed", extra={"details": {"error": str(e)}})
            return "error", {}

    def process_prompt(self, user_input: str) -> str:
        """
        Processes a user prompt by selecting and executing a tool.
        """
        self.logger.info("prompt_received", extra={"details": {"prompt": user_input}})

        # Fallback behavior if no tools are loaded
        if not self.tools:
            self.logger.warning("no_tools_loaded", extra={
                "details": {"response": self._get_fallback_response()}
            })
            return self._get_fallback_response()

        try:
            # 1. Build the list of OpenAI schemas from our tool instances
            openai_schemas = [tool.to_openai_schema() for tool in self.tools.values()]

            # --- DEBUG: Commented out for cleaner logs ---
            # print(f"--- DEBUG: Sending OpenAI Schemas to LLM for {self.persona_name} ---")
            # import json
            # print(json.dumps(openai_schemas, indent=2))
            # print("--- END DEBUG SCHEMAS ---")

            # 2. Call the LLM to select a function and its arguments
            function_name, arguments = self._call_llm_with_functions(user_input, openai_schemas)
            
            self.logger.info("tool_selected", extra={
                "details": {"tool_name": function_name, "arguments": arguments}
            })

            if function_name == "unknown":
                self.logger.info("unknown_command_response", extra={
                    "details": {"response": f"I'm not sure how to handle that request. I am {self.persona_config.get('description')}."}
                })
                return f"I'm not sure how to handle that request. I am {self.persona_config.get('description')}."

            if function_name == "error":
                self.logger.error("tool_execution_failed", extra={
                    "details": {"error": arguments}
                })
                return f"An error occurred during function selection: {arguments}"

            # 3. Execute the tool
            tool_to_call = self.tools.get(function_name)
            if not tool_to_call:
                 error_msg = f"Error: Tool '{function_name}' not found in agent's toolset."
                 self.logger.error("tool_not_found_in_set", extra={"details": {"tool_name": function_name}})
                 return error_msg
            
            result = tool_to_call.run(**arguments)

            # 4. Synthesize and return the response
            response = self._synthesize_response(result)
            self.logger.info("response_generated", extra={"details": {"response": response}})
            return response

        except Exception as e:
            self.logger.error("prompt_processing_failed", extra={
                "details": {"error": str(e), "prompt": user_input}
            })
            error_message = f"An error occurred during processing: {e}"
            return self._synthesize_response(error_message)

    def run_interactive_loop(self):
        """The main interactive loop for running the agent from the command line."""
        print(f"=== {self.persona_config.get('name')} started. Type 'exit' to quit. ===")
        while True:
            try:
                user_input = input(">> ")
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                response = self.process_prompt(user_input)
                print(f"Agent: {response}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                self.logger.error("interactive_loop_error", extra={"details": {"error": str(e)}})
                print(f"An unexpected error occurred: {e}")