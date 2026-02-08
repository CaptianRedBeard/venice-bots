import sys
import os
import json
import logging
import datetime
from typing import Optional, List, Dict, Any

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# --- Core Framework Imports ---
from core_tools.knowledge_base import KnowledgeBase
from core_tools.config import get_venice_client, get_model_for_role
from core_tools.tool_registry import ToolRegistry
from core_tools.llm_function_caller import LLMFunctionCaller
# --- NEW: Import the centralized logger ---
from symphony.symphony_logger import get_logger

# --- Default Tool Initialization Imports ---
from core_tools.summarizer_tool import initialize_and_register as init_summarizer_tool


class AgentShell:
    """
    A robust, dynamically configurable agent shell designed for the Symphony framework.

    This agent is a "doer" that is completely decoupled from a hardcoded list of tools.
    It builds its usable toolset at runtime by merging a default list from its
    configuration with any tools injected by a higher-level component (like a Conductor).

    Attributes:
        persona_config (dict): The configuration loaded from the agent's config.json.
        tool_registry (ToolRegistry): The central registry holding the agent's available tools.
        llm_caller (LLMFunctionCaller): The stateless "brain" for parsing user intent.
        logger (logging.Logger): Configured logger from the centralized SymphonyLogger.
    """

    def __init__(
        self,
        persona_name: str = "agent_v12_the_shell",
        tool_registry: Optional[ToolRegistry] = None,
        injected_tool_names: Optional[List[str]] = None
    ):
        """
        Initializes the Agent V12 Shell.

        Args:
            persona_name (str): The name of the persona, used to load its config and data.
            tool_registry (Optional[ToolRegistry]): An existing ToolRegistry instance.
                If None, a new one will be created.
            injected_tool_names (Optional[List[str]]): A list of tool names to be
                dynamically loaded and added to the agent's toolset. This takes
                precedence over the default tools in the config.
        """
        # 1. Load Persona Configuration
        self.kb = KnowledgeBase(persona_name=persona_name)
        self.persona_config = self.kb.config
        
        # 2. Get the centralized logger
        self.logger = get_logger(self.persona_config.get('name', 'AgentShell'))

        self.logger.info("agent_initialized", extra={
            "details": {
                "persona": persona_name,
                "default_tools": self.persona_config.get("default_tools", []),
                "injected_tools": injected_tool_names or []
            }
        })

        # 3. Initialize Core Components
        self.llm_client = get_venice_client()
        self.tool_registry = tool_registry if tool_registry is not None else ToolRegistry()
        self.llm_caller = LLMFunctionCaller(role="function_calling")

        # 4. Load Tools Dynamically
        self._load_tools(injected_tool_names)

        self.logger.info("agent_setup_complete", extra={
            "details": {
                "final_toolset": self.tool_registry.list_tools()
            }
        })

    def _load_tools(self, injected_tool_names: Optional[List[str]]):
        """
        Loads tools into the agent's registry by merging config defaults with injected tools.
        """
        # Source 1: Default tools from config.json
        default_tool_names = self.persona_config.get("default_tools", [])

        # Source 2: Injected tools from Conductor (takes precedence)
        final_tool_names = list(default_tool_names)
        if injected_tool_names:
            final_tool_names.extend(injected_tool_names)

        # Remove duplicates while preserving order
        seen = set()
        unique_tool_names = [name for name in final_tool_names if not (name in seen or seen.add(name))]

        # Initialize and register the tools
        for tool_name in unique_tool_names:
            try:
                if tool_name == "summarizer_tool":
                    init_summarizer_tool(self.tool_registry)
                else:
                    self.logger.warning(f"unknown_tool_initializer", extra={
                        "details": {"tool_name": tool_name}
                    })
            except Exception as e:
                self.logger.error("tool_initialization_failed", extra={
                    "details": {"tool_name": tool_name, "error": str(e)}
                })

    def _synthesize_response(self, tool_output: Any) -> str:
        """Uses an LLM to synthesize the raw tool output into a user-friendly response."""
        system_prompt = self.persona_config.get('system_prompt', "You are a helpful assistant.")
        synthesis_prompt = f"""Summarize the following data for the user based on your persona. Do not add information that is not present in the data. If the data is an error message, report it clearly.
Data:
{json.dumps(tool_output, indent=2)}
Summary:"""
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

    def process_prompt(self, user_input: str) -> str:
        """
        Processes a user prompt through the linear orchestration flow.
        
        Args:
            user_input (str): The raw input string from the user.
            
        Returns:
            str: The agent's final, synthesized response.
        """
        self.logger.info("prompt_received", extra={
            "details": {"prompt": user_input}
        })
        
        # Fallback behavior if no tools are loaded
        if not self.tool_registry.list_tools():
            self.logger.warning("no_tools_loaded", extra={
                "details": {"response": self._get_fallback_response()}
            })
            return self._get_fallback_response()

        try:
            # 1. Parse user intent into a tool call
            all_schemas = self.tool_registry.get_all_schemas()
            tool_name, args = self.llm_caller.parse(user_input, all_schemas)
            
            self.logger.info("tool_selected", extra={
                "details": {"tool_name": tool_name, "arguments": args}
            })

            # 2. Handle unknown commands
            if tool_name == "unknown":
                persona_desc = self.persona_config.get('description', 'a helpful assistant')
                response = f"I'm not sure how to handle that request. I am {persona_desc}."
                self.logger.info("unknown_command_response", extra={
                    "details": {"response": response}
                })
                return response

            # 3. Execute the tool
            tool_output = self.tool_registry.call(tool_name, **args)

            # 4. Synthesize and return the response
            response = self._synthesize_response(tool_output)
            self.logger.info("response_generated", extra={
                "details": {"response": response}
            })
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
                self.logger.error("interactive_loop_error", extra={
                    "details": {"error": str(e)}
                })
                print(f"An unexpected error occurred: {e}")