#!/usr/bin/env python3
"""
Agent V10: The Tool-First Agent
A reliable agent that uses deterministic intent classification for tool use.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_tools.config import get_venice_client
    from core_tools.tool_registry import ToolRegistry
    from core_tools.knowledge_base import KnowledgeBase
    from core_tools.tool_first_orchestrator import ToolFirstOrchestrator
    from core_tools.file_system_tool import read_file, list_directory, find_files
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def main():
    print("=== Agent V10 - The Tool-First Agent ===")

    # Initialize tool registry and register tools
    tool_registry = ToolRegistry()
    tool_registry.register_tool(read_file)
    tool_registry.register_tool(list_directory)
    tool_registry.register_tool(find_files)

    # Get Venice client
    try:
        client = get_venice_client()
        print("✓ Venice client initialized")
        print(f"✓ Registered {len(tool_registry.tools)} tools")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        sys.exit(1)

    # Initialize knowledge base with the new persona configuration
    try:
        persona_name = "efficient_analyst"
        knowledge_base = KnowledgeBase(persona_name)
        persona_config = knowledge_base.config
        print(f"✓ Knowledge base initialized (persona: {persona_name})")
        print(f"✓ Description: {persona_config.get('description', 'No description')}")
    except Exception as e:
        print(f"✗ Failed to load persona configuration: {e}")
        sys.exit(1)

    # Initialize the new Tool-First Orchestrator
    orchestrator = ToolFirstOrchestrator(tool_registry=tool_registry, llm_client=client)
    print("✓ Tool-First Orchestrator initialized")
    
    synthesis_model = persona_config.get('models', {}).get('synthesis', 'default-model')
    print(f"✓ Synthesis model configured: {synthesis_model}")

    print(f"\nAgent V10 The Tool-First Agent started. Type 'exit' to quit.")
    print(f"This agent uses deterministic intent classification for improved reliability.")
    print()

    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if not user_input:
                continue

            # Use the orchestrator to process the request
            print("Agent: Processing...")
            final_response = orchestrator.run(user_input, persona_config)
            print(f"Agent: {final_response}\n")

        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during processing: {e}")

if __name__ == "__main__":
    main()