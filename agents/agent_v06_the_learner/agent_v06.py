import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_tools.config import get_venice_client
    from core_tools.tool_registry import ToolRegistry
    from core_tools.knowledge_base_v06 import KnowledgeBase
    from core_tools.orchestrator import CognitiveOrchestrator
    from core_tools.tools import get_current_time, add_numbers
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    print("=== Agent V6 - The Learner (Enhanced) ===")
    
    # Initialize tool registry and register tools
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
    knowledge_base = KnowledgeBase("venice_assistant")
    print("✓ Knowledge base initialized (persona: venice_assistant)")
    
    # Show existing facts
    existing_facts = knowledge_base.get_all_facts()
    if existing_facts:
        print(f"✓ Loaded {len(existing_facts)} existing facts from memory")
        print(f"✓ Recent facts: {existing_facts[-3:] if len(existing_facts) > 3 else existing_facts}")
    else:
        print("✓ No existing facts found - starting fresh")
    
    # Initialize cognitive orchestrator
    orchestrator = CognitiveOrchestrator(client, tool_registry, knowledge_base)
    print("✓ Cognitive Orchestrator initialized")
    
    print("\nAgent V6 The Learner started. Type 'exit' to quit.")
    print("This agent remembers facts about you and learns from conversations.")
    print("Try asking about your name, location, or preferences after telling me!\n")
    
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