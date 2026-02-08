import os
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List  # <-- FIX: Added List to the import

class AgentRegistry:
    """
    Manages the registration and retrieval of agent configurations.
    This version is designed to look for a 'personas' directory at the project root.
    """
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        # --- FIX: Explicitly set the path to the 'personas' dir at the project root ---
        self.personas_path = Path(__file__).resolve().parent.parent / "personas"

    def register_agents_from_path(self, personas_dir_name: str = "personas"):
        """
        Scans the configured personas path and registers all .yaml files.
        """

        # --- DEBUG: Print the exact path being used ---
        ## print(f"--- AgentRegistry: Searching for personas in: {self.personas_path} ---")
        
        if not self.personas_path.is_dir():
            # --- DEBUG: Raise an error if the path is not a directory ---
            raise FileNotFoundError(f"AgentRegistry: Personas directory not found at {self.personas_path}")

        for file_path in self.personas_path.glob("*.yaml"):
            agent_name = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self.agents[agent_name] = config
                print(f"✓ Registered agent: {agent_name} from {file_path}")
            except Exception as e:
                print(f"Failed to register agent from {file_path}: {e}")

    def get_agent_config(self, agent_name: str) -> Dict[str, Any] | None:
        """
        Retrieves the configuration for a specific agent.
        """
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """
        Returns a list of all registered agent names.
        """
        return list(self.agents.keys())