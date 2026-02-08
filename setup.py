#!/usr/bin/env python3
"""
Project Setup Manager.
Provides a simple interface to initialize the environment for specific agents.
Automatically discovers all Symphony agents in the 'agents/' directory.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

# --- Auto-Discovery Logic ---

def discover_agents() -> Dict[str, str]:
    """
    Scans the 'agents/' directory to find all agents with a setup.py script.
    Assumes all discovered agents are part of the Symphony standard (v12+).
    """
    agents_dir = Path("agents")
    if not agents_dir.is_dir():
        print("Error: 'agents/' directory not found.")
        return {}

    available_agents = {}
    for agent_path in agents_dir.iterdir():
        if agent_path.is_dir():
            setup_script = agent_path / "setup.py"
            if setup_script.is_file():
                agent_name = agent_path.name
                available_agents[agent_name] = str(setup_script)
    
    return available_agents

# --- Core Logic ---

def run_agent_setup(agent_name: str, registry: Dict[str, str]) -> Tuple[bool, str]:
    """Finds and runs the setup script for a given agent."""
    if agent_name not in registry:
        return False, f"No setup script registered for '{agent_name}'."

    script_path = registry[agent_name]
    print(f"--- Running setup for: {agent_name} ---")
    try:
        # Use subprocess to run the script in its own context
        subprocess.run([sys.executable, script_path], check=True)
        return True, f"Setup for '{agent_name}' completed successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Setup for '{agent_name}' failed with exit code {e.returncode}."
    except FileNotFoundError:
        return False, f"Could not find python interpreter or script at '{script_path}'."

def main():
    """Main function to display the menu and process user choice."""
    print("Project Symphony - Agent Setup Manager")
    print("======================================")
    print("This script helps you initialize the environment for a specific agent.")

    # Discover agents automatically
    available_agents = discover_agents()

    if not available_agents:
        print("\nNo agents with setup scripts were found in the 'agents/' directory.")
        return

    print("\n--- Available Agents ---")
    for name in sorted(available_agents.keys()):
        print(f"  - {name}")

    print(f"\nEnter the name of the agent you want to set up (e.g., '{list(available_agents.keys())[0]}').")
    print("Type 'exit' to quit.")
    choice = input("Agent Name: ").strip()

    if choice.lower() == 'exit':
        print("Exiting setup manager.")
        return

    if not choice:
        print("No agent selected. Exiting.")
        return

    success, message = run_agent_setup(choice, available_agents)

    # Print the final result
    if success:
        print(f"\n✅ Success: {message}")
    else:
        print(f"\n❌ Failure: {message}")


if __name__ == "__main__":
    main()