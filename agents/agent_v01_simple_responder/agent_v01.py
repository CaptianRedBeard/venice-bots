import sys
import os
from pathlib import Path

# Add project root to Python path for core_tools import
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_tools.config import get_api_key
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root or core_tools is installed.")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("OpenAI library not installed. Installing now...")
    print("Run: pip install openai")
    sys.exit(1)

def main():
    try:
        api_key = get_api_key()
    except (FileNotFoundError, ValueError) as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Initialize OpenAI client with Venice's base URL
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.venice.ai/api/v1"
    )
    
    print("Agent V1 Simple Responder started. Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Make API request using OpenAI-compatible interface
            response = client.chat.completions.create(
                model="venice-uncensored",
                messages=[
                    {"role": "user", "content": user_input}
                ],
                # Optional: Venice-specific parameters
                extra_body={
                    "venice_parameters": {
                        "include_venice_system_prompt": True,
                        "enable_web_search": "off"
                    }
                }
            )
            
            agent_response = response.choices[0].message.content
            print(f"Agent: {agent_response}")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during conversation: {e}")
            # Continue loop for resilience

if __name__ == "__main__":
    main()