import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import everything we need from core_tools
try:
    from core_tools import get_venice_client, get_default_model, get_venice_parameters
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    print("=== Agent V2 - Using core_tools ===")
    
    # Get configured client from core_tools
    try:
        client = get_venice_client()
        model = get_default_model()
        venice_params = get_venice_parameters()
        print(f"✓ Connected to Venice using model: {model}")
        print(f"✓ Venice parameters: {venice_params}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        sys.exit(1)
    
    print("\nAgent V2 Simple Responder started. Type 'exit' to quit.")
    print("Configuration handled by core_tools module.\n")
    
    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Make API request using configured client from core_tools
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": user_input}
                ],
                extra_body={
                    "venice_parameters": venice_params
                }
            )
            
            agent_response = response.choices[0].message.content
            print(f"Agent: {agent_response}")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during conversation: {e}")

if __name__ == "__main__":
    main()