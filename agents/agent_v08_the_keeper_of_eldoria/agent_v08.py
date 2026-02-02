#!/usr/bin/env python3
"""
Agent V08: The Keeper of Eldoria (Specialist with Persona-Based Memory)
Demonstrates the agent_v07 architecture with a creative world-building persona.
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
    from core_tools.brainstorm_tool import brainstorm
    from core_tools.creative_tool import generate_description, expand_concept
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    print("=== Agent V08 - The Keeper of Eldoria (Specialist Persona) ===")
    
    # Initialize tool registry and register tools
    tool_registry = ToolRegistry()
    tool_registry.register_tool(get_current_time)
    tool_registry.register_tool(add_numbers)
    tool_registry.register_tool(brainstorm)
    tool_registry.register_tool(generate_description)
    tool_registry.register_tool(expand_concept)
    
    # Get Venice client
    try:
        client = get_venice_client()
        print("✓ Venice client initialized")
        print(f"✓ Registered {len(tool_registry.tools)} tools")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        sys.exit(1)
    
    # Initialize knowledge base with persona configuration
    try:
        persona_name = "keeper_of_eldoria"
        knowledge_base = KnowledgeBase(persona_name)
        print(f"✓ Knowledge base initialized (persona: {persona_name})")
        print(f"✓ Description: {knowledge_base.config.get('description', 'No description')}")
        print(f"✓ Role: {knowledge_base.config.get('role', 'No role')}")
        print(f"✓ Memory config: {knowledge_base.config.get('memory_config', {})}")
        print(f"✓ ACL: {knowledge_base.config.get('acl', {})}")
    except Exception as e:
        print(f"✗ Failed to load persona configuration: {e}")
        sys.exit(1)
    
    # Show existing facts
    existing_facts = knowledge_base.get_all_facts()
    if existing_facts:
        print(f"✓ Loaded {len(existing_facts)} existing facts from memory")
        print(f"✓ Recent facts: {existing_facts[-3:] if len(existing_facts) > 3 else existing_facts}")
    else:
        print("✓ No existing facts found - starting fresh")
    
    # Initialize cognitive orchestrator with persona
    orchestrator = CognitiveOrchestrator(client, tool_registry, persona_name=persona_name)
    print("✓ Cognitive Orchestrator initialized")
    print(f"✓ System prompt loaded: {knowledge_base.config.get('system_prompt', 'No system prompt')[0:50]}...")
    
    memory_config = knowledge_base.config.get('memory_config', {})
    default_recall = memory_config.get('default_recall_target', 'self')
    
    print(f"\nAgent V08 The Keeper of Eldoria started. Type 'exit' to quit.")
    print(f"This agent uses the '{persona_name}' persona with specialist memory access.")
    print(f"Default recall target: {default_recall}\n")
    
    while True:
        try:
            user_input = input("User: ").strip()
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Use cognitive orchestrator to process with memory
            print("Agent: Thinking and learning...")
            final_response = orchestrator.plan_and_execute(user_input)
            print(f"Agent: {final_response}\n")
            
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during processing: {e}")

if __name__ == "__main__":
    main()
