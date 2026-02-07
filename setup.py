#!/usr/bin/env python3
"""
Project Setup Manager.
Provides a simple interface to initialize the environment for specific agents.
"""

import subprocess
import sys
from pathlib import Path

# A registry of agents that have an associated setup script.
# We will populate this as we update agents to be self-initializing.
AGENT_SETUP_REGISTRY = {
    "agent_v11_the_captains_log": "agents/agent_v11_the_captains_log/setup.py",
    # Future agents will be added here, e.g.:
    # "agent_v12_task_master": "agents/agent_v12_task_master/setup.py",
}

def run_agent_setup(agent_name):
    """Finds and runs the setup script for a given agent."""
    if agent_name not in AGENT_SETUP_REGISTRY:
        print(f"Error: No setup script registered for '{agent_name}'.")
        print("Available agents with setup scripts:")
        for name in sorted(AGENT_SETUP_REGISTRY.keys()):
            print(f"  - {name}")
        return

    script_path = AGENT_SETUP_REGISTRY[agent_name]
    if not Path(script_path).is_file():
        print(f"Error: Setup script not found at '{script_path}'.")
        return

    print(f"--- Running setup for: {agent_name} ---")
    try:
        # Use subprocess to run the script in its own context
        subprocess.run([sys.executable, script_path], check=True)
        print(f"\n✅ Setup for '{agent_name}' completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Setup for '{agent_name}' failed with exit code {e.returncode}.")
    except FileNotFoundError:
        print(f"Error: Could not find python interpreter or script at '{script_path}'.")

def main():
    """Main function to display the menu and process user choice."""
    print("Project Chimera - Agent Setup Manager")
    print("=====================================")
    print("This script helps you initialize the environment for a specific agent.")
    
    if not AGENT_SETUP_REGISTRY:
        print("\nNo agents are currently registered for setup.")
        print("This feature will be available as agents are updated.")
        return

    print("\nAvailable agents to initialize:")
    for i, name in enumerate(sorted(AGENT_SETUP_REGISTRY.keys()), 1):
        print(f"  {i}. {name}")
    
    print("\nEnter the name of the agent you want to set up.")
    choice = input("Agent Name: ").strip()

    if choice:
        run_agent_setup(choice)
    else:
        print("No agent selected. Exiting.")

if __name__ == "__main__":
    main()