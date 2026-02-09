import yaml
import os
import sys
from pathlib import Path
from typing import Any, Dict
import logging
import inspect


# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# --- Framework Imports ---
from symphony.agent_shell import AgentShell
from symphony.agent_registry import AgentRegistry
from symphony.tool_registry import ToolRegistry
from symphony.context_manager import get_context_manager 
from symphony.symphony_logger import get_logger


# NOTE: ModelManager is a placeholder for future functionality.
# For this sprint, we will instantiate agents directly.
# from core_tools.model_manager import ModelManager

class Conductor:
    """
    Orchestrates multi-agent workflows defined in YAML files.
    The Conductor parses a workflow, executes its steps sequentially, manages state between steps, and logs the entire process.
    """
    def __init__(self, agent_registry: AgentRegistry, tool_registry: ToolRegistry):
        """ Initializes the Conductor. Args: agent_registry (AgentRegistry): The registry to find agents. tool_registry (ToolRegistry): The shared tool registry for agents. """
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.logger = get_logger("conductor")
        # Explicitly register all available tools upon initialization.
        self._register_available_tools()
        self.logger.info("conductor_initialized", extra={
            "details": {"message": "Conductor is ready to orchestrate workflows."}
        })

    def _register_available_tools(self):
        """Registers all known tools with the tool registry."""
        self.logger.info("registering_conductor_tools", extra={
            "details": {"tools": ["file_system_tool"]}
        })
        try:
            from symphony_tools.file_system_tool import initialize_and_register as init_file_system_tool
            init_file_system_tool(self.tool_registry)
        except ImportError as e:
            self.logger.error("conductor_tool_import_failed", extra={
                "details": {"tool": "file_system_tool", "error": str(e)}
            })
        except Exception as e:
            self.logger.error("conductor_tool_registration_failed", extra={
                "details": {"tool": "file_system_tool", "error": str(e)}
            })

    def load_agent(self, agent_name: str):
        """
        Public method to load and return a single agent instance for interactive use.
        This is a convenience method for testing and CLI tools.
        """
        self.logger.info(f"Loading agent '{agent_name}' for direct use.")
        return self._get_agent_instance(agent_name)

    # ... (the rest of the Conductor class is unchanged) ...
    def execute_workflow(self, workflow_path: str, initial_input: str) -> Dict[str, Any]:
        """ Parses and executes a workflow from a YAML file. Args: workflow_path (str): The file path to the workflow YAML. initial_input (str): The initial input to start the workflow. Returns: Dict[str, Any]: A dictionary containing the final workflow state, including the final output and any errors. """
        self.logger.info("workflow_started", extra={
            "details": {"workflow_path": workflow_path, "initial_input": initial_input}
        })
        try:
            with open(workflow_path, 'r') as f:
                workflow = yaml.safe_load(f)
        except Exception as e:
            self.logger.error("workflow_load_failed", extra={
                "details": {"workflow_path": workflow_path, "error": str(e)}
            })
            return {"status": "failed", "error": f"Could not load workflow file: {e}"}
        workflow_state = {"input": initial_input}
        final_output = None
        for i, step in enumerate(workflow.get('steps', [])):
            step_id = step.get('id', f'step_{i+1}')
            self.logger.info("step_started", extra={
                "details": {"step_id": step_id, "step_type": step.get('type')}
            })
            try:
                step_type = step.get('type')
                if step_type == 'tool':
                    # For this sprint, tool execution is conceptual.
                    # In a future sprint, the Conductor would call tools directly.
                    tool_name = step.get('name')
                    self.logger.info("tool_execution_conceptual", extra={
                        "details": {"tool_name": tool_name, "input": workflow_state['output']}
                    })
                    final_output = f"[Conceptual Tool Output from {tool_name}]"
                elif step_type == 'agent':
                    agent_name = step.get('agent')
                    agent = self._get_agent_instance(agent_name)
                    prompt = step.get('prompt').format(**workflow_state)
                    self.logger.info("agent_execution_started", extra={
                        "details": {"agent_name": agent_name, "prompt": prompt}
                    })
                    final_output = agent.process_prompt(prompt)
                    self.logger.info("agent_execution_finished", extra={
                        "details": {"agent_name": agent_name, "output": final_output}
                    })
                else:
                    raise ValueError(f"Unknown step type: {step_type}")
                # Update state for the next step
                workflow_state['output'] = final_output
            except Exception as e:
                self.logger.error("step_failed", extra={
                    "details": {"step_id": step_id, "error": str(e)}
                })
                return {"status": "failed", "error": f"Step {step_id} failed: {e}", "state": workflow_state}
        self.logger.info("workflow_completed", extra={
            "details": {"final_output": final_output}
        })
        return {"status": "completed", "output": final_output, "final_state": workflow_state}

    def _get_agent_instance(self, agent_name: str) -> AgentShell:
        """ Retrieves or creates an agent instance, passing the ContextManager and ACL. """
        self.logger.info("agent_instance_requested", extra={"details": {"agent_name": agent_name}})
        agent_config = self.agent_registry.get_agent_config(agent_name)
        if not agent_config:
            # ... (error handling) ...
            return AgentShell(persona_name=agent_name, persona_config={}, instantiated_tools={})

        # --- Get ContextManager and ACL ---
        context_manager = get_context_manager()
        agent_acl = agent_config.get('acl', {'access_level': 'public'})

        # --- Instantiate Tools (logic is the same) ---
        default_tools = agent_config.get('default_tools', [])
        # print(f"DEBUG: Tools requested by agent '{agent_name}': {default_tools}") # <--- DEBUG
        instantiated_tools = {}
        for tool_name in default_tools:
            try:
                # Get the tool class from the now-populated registry.
                tool_class = self.tool_registry.get(tool_name)
                
                # --- ROBUST FIX: Inspect the tool's __init__ signature ---
                sig = inspect.signature(tool_class.__init__)
                if 'persona_name' in sig.parameters:
                    # Old tool style: requires persona_name
                    tool_instance = tool_class(persona_name=agent_name)
                else:
                    # New tool style: requires no arguments
                    tool_instance = tool_class()
                
                instantiated_tools[tool_name] = tool_instance
                self.logger.info("tool_instantiated", extra={
                    "details": {"tool_name": tool_name, "for_agent": agent_name}
                })
            except Exception as e:
                self.logger.error("tool_instantiation_failed", extra={
                    "details": {"tool_name": tool_name, "error": str(e)}
                })
        
        # print(f"DEBUG: Instantiated tools to be passed to agent: {list(instantiated_tools.keys())}") # <--- DEBUG
        
        # --- Create and Return Agent with new parameters ---
        return AgentShell(
            persona_name=agent_name,
            persona_config=agent_config,
            instantiated_tools=instantiated_tools,
            context_manager=context_manager,
            agent_acl=agent_acl
        )
