import sys
import re
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_tools.config import get_api_key
    from core_tools.conversation import ConversationHistory
    from core_tools.tool_registry import ToolRegistry
    from core_tools.tools import get_current_time, add_numbers
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("OpenAI library not installed. Install with: pip install openai")
    sys.exit(1)

def parse_tool_call(response_text):
    """Parse a tool call from the AI response with robust regex matching."""
    # Look for the exact pattern: TOOL_CALL: function_name|arg1=value1|arg2=value2
    pattern = r'TOOL_CALL:\s*(\w+)(?:\|([^|]*(?:\|[^|]*)*))?'
    match = re.search(pattern, response_text)
    
    if not match:
        return None, None
    
    tool_name = match.group(1).strip()
    args_str = match.group(2) if match.group(2) else ""
    
    args = {}
    if args_str:
        # Split by | and parse key=value pairs
        arg_pairs = args_str.split('|')
        for pair in arg_pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove any trailing text or newlines
                value = re.sub(r'[^0-9.\-+]', '', value)
                if value:
                    args[key] = value
    
    return tool_name, args

def main():
    print("=== Agent V4 - Tool User (Enhanced) ===")
    
    # Initialize tool registry and register tools
    tool_registry = ToolRegistry()
    tool_registry.register_tool(get_current_time)
    tool_registry.register_tool(add_numbers)
    
    # Initialize conversation history
    conversation = ConversationHistory(max_tokens=4000, max_messages=20)
    
    # Build stricter system prompt
    tools_prompt = tool_registry.get_tools_for_prompt()
    system_prompt = f"""You are a helpful AI assistant that can use specific tools to answer questions and perform tasks.

Available tools:
{tools_prompt}

CRITICAL INSTRUCTIONS FOR TOOL USAGE:

When you need to use a tool, output ONLY the tool call, NOTHING ELSE:
- get_current_time: TOOL_CALL: get_current_time|
- add_numbers: TOOL_CALL: add_numbers|a=5|b=3

The format MUST be: TOOL_CALL: function_name|arg1=value1|arg2=value2
For functions with no arguments, add the pipe: TOOL_CALL: function_name|

DO NOT add any explanation, greeting, or additional text. Just the tool call line.

If you don't need to use a tool, respond normally with your answer."""
    
    conversation.add_message('system', system_prompt)
    
    # Get Venice client
    try:
        api_key = get_api_key()
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.venice.ai/api/v1"
        )
        print("✓ Venice client initialized")
        print(f"✓ Registered {len(tool_registry.tools)} tools")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        sys.exit(1)
    
    print("\nAgent V4 Tool User started. Type 'exit' to quit.")
    print("This agent can use tools to help answer your questions.\n")
    
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
                messages=messages,
                temperature=0.1  # Lower temperature for more consistent tool formatting
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"Raw AI response: {repr(ai_response)}")  # Debug output
            
            # Parse for tool call
            tool_name, tool_args = parse_tool_call(ai_response)
            
            if tool_name:
                # This is a tool call
                print(f"Agent: Calling tool {tool_name} with args: {tool_args}")
                
                try:
                    # Convert string arguments to appropriate types
                    processed_args = {}
                    for key, value in tool_args.items():
                        # Try to convert to int or float
                        try:
                            if '.' in value and value.replace('.', '').replace('-', '').isdigit():
                                processed_args[key] = float(value)
                            elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                                processed_args[key] = int(value)
                            else:
                                processed_args[key] = value
                        except (ValueError, AttributeError):
                            processed_args[key] = value
                    
                    # Call the tool
                    result = tool_registry.call_tool(tool_name, **processed_args)
                    
                    print(f"Tool Result: {result}")
                    
                    # Add tool call and result to conversation
                    conversation.add_message('assistant', ai_response)
                    conversation.add_message('system', f"Tool {tool_name} returned: {result}")
                    
                except Exception as e:
                    error_msg = f"Error calling tool {tool_name}: {str(e)}"
                    print(error_msg)
                    conversation.add_message('assistant', ai_response)
                    conversation.add_message('system', error_msg)
            else:
                # Normal response
                print(f"Agent: {ai_response}")
                conversation.add_message('assistant', ai_response)
            
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