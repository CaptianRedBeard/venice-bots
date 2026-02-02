import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_tools.config import get_api_key
    from core_tools.conversation import ConversationHistory
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("OpenAI library not installed. Install with: pip install openai")
    sys.exit(1)

def main():
    print("=== Agent V3 - Conversationalist with History ===")
    
    # Initialize conversation history with token limit
    conversation = ConversationHistory(max_tokens=4000, max_messages=20)
    
    # Add system message
    conversation.add_message('system', "You are a helpful AI assistant. Be conversational and engaging.")
    
    # Get Venice client
    try:
        api_key = get_api_key()
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.venice.ai/api/v1"
        )
        print("✓ Venice client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        sys.exit(1)
    
    print("\nAgent V3 Conversationalist started. Type 'exit' to quit.")
    print("Conversation context is maintained across messages.\n")
    
    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Add user message to history
            conversation.add_message('user', user_input)
            
            # Get current conversation history
            messages = conversation.get_history()
            
            # Send to Venice API
            response = client.chat.completions.create(
                model="venice-uncensored",
                messages=messages
            )
            
            agent_response = response.choices[0].message.content
            print(f"Agent: {agent_response}")
            
            # Add agent response to history
            conversation.add_message('assistant', agent_response)
            
            # Show current history status
            history = conversation.get_history()
            print(f"[History: {len(history)} messages]", end="\n\n")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during conversation: {e}")

if __name__ == "__main__":
    main()