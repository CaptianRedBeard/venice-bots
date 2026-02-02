#!/usr/bin/env python3
"""
Agent V08 Debug Version - Testing with minimal tools
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
    from core_tools.orchestrator import CognitiveOrchestrator
    from core_tools.tools import get_current_time, add_numbers
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    print("=== Agent V08 DEBUG VERSION ===")
    
    # Initialize tool registry with only basic tools
    tool_registry = ToolRegistry()
    tool_registry.register_tool(get_current_time)
    tool_registry.register_tool(add_numbers)
    
    # Get Venice client
    try:
        client = get_venice_client()
        print("✓ Venice client initialized")
        print(f"✓ Registered {len(tool_registry.tools)} tools")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        sys.exit(1)
    
    # Initialize knowledge base
    try:
        persona_name = "keeper_of_eldoria"
        knowledge_base = KnowledgeBase(persona_name)
        print(f"✓ Knowledge base initialized")
    except Exception as e:
        print(f"✗ Failed to load persona: {e}")
        sys.exit(1)
    
    # Initialize cognitive orchestrator
    orchestrator = CognitiveOrchestrator(client, tool_registry, persona_name=persona_name)
    print("✓ Cognitive Orchestrator initialized")
    
    print(f"\nDEBUG VERSION - Minimal tools only. Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("User: ").strip()
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("Agent: Processing...")
            final_response = orchestrator.plan_and_execute(user_input)
            print(f"Agent: {final_response}\n")
            
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during processing: {e}")

if __name__ == "__main__":
    main()
