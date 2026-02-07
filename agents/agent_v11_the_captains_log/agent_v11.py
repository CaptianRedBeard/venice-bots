import sys
import os
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# --- 1. Load Persona Configuration ---
from core_tools.knowledge_base import KnowledgeBase
from core_tools.config import get_venice_client, get_model_for_role

# Load persona-specific data
kb = KnowledgeBase(persona_name="captains_log")
persona_config = kb.config
llm_client = get_venice_client()

# --- 2. Initialize Tools and Registry ---
from core_tools.tool_registry import ToolRegistry
from core_tools.llm_function_caller import LLMFunctionCaller
from core_tools.journal_manager_tool import initialize_and_register as init_journal_tool
from core_tools.summarizer_tool import initialize_and_register as init_summarizer_tool

# The registry holds the agent's available tools
tool_registry = ToolRegistry()
init_journal_tool(tool_registry, persona_name="captains_log")
init_summarizer_tool(tool_registry)

# The LLM caller is our "brain" for parsing user intent
llm_caller = LLMFunctionCaller(role="function_calling")

# --- 3. Simplified Orchestration Logic ---
def synthesize_response(tool_output: any) -> str:
    """Uses an LLM to synthesize the raw tool output into a user-friendly response."""
    system_prompt = persona_config.get('system_prompt', "You are a helpful assistant.")
    synthesis_prompt = f"""Summarize the following data for the user based on your persona. Do not add information that is not present in the data. If the data is an error message, report it clearly.
    
    Data: {json.dumps(tool_output, indent=2)}
    
    Summary:"""
    
    try:
        model = get_model_for_role('synthesis')
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": synthesis_prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I was able to execute the tool, but I had trouble formatting the response. Here is the raw data:\n{tool_output}"

def run_orchestration(user_input: str) -> str:
    """A simple, linear orchestration flow."""
    try:
        # 1. Handle summarization of long text
        if len(user_input) > 300:
            model = get_model_for_role('synthesis')
            response = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond only with 'yes' or 'no'."},
                    {"role": "user", "content": f"The user wants to add this note to their journal: '{user_input}'. Should I ask if they want to summarize it because it's long?"}
                ],
                temperature=0.1
            )
            if response.choices[0].message.content.strip().lower() == 'yes':
                return "That's a long note. Should I log it as-is, or summarize it for you? (Reply with 'summarize' or 'log as-is')"

        # 2. Handle user choice for summarization
        if user_input.lower() in ["summarize", "log as-is"]:
            if not hasattr(run_orchestration, '_pending_long_text'):
                return "I don't have a previous long text to summarize or log. Please provide it again."
            
            if user_input.lower() == "summarize":
                summarizer_tool = tool_registry.get("summarize")
                summary = summarizer_tool.summarize(text_to_summarize=run_orchestration._pending_long_text)
                user_input = f"Add '{summary}' to my journal."
            elif user_input.lower() == "log as-is":
                user_input = run_orchestration._pending_long_text
            
            del run_orchestration._pending_long_text

        # 3. Get available headers for dynamic parsing
        # For simplicity, we'll always assume 'daily' and 'today' for this check
        available_headers = []
        try:
            available_headers = tool_registry.call("get_headers", file_type='daily', target_date_str='today')
        except Exception:
            # It's okay if the file doesn't exist, we'll proceed without headers
            pass

        # 4. Parse user intent into a tool call
        all_schemas = tool_registry.get_all_schemas()
        tool_name, args = llm_caller.parse(user_input, all_schemas, available_headers=available_headers)

        # 5. Handle unknown commands
        if tool_name == "unknown":
            persona_desc = persona_config.get('description', 'a helpful assistant')
            return f"I'm not sure how to handle that request. I am {persona_desc}."

        # 6. Store pending text if it's a long append request
        if len(user_input) > 300 and tool_name == "append_to_section":
            run_orchestration._pending_long_text = user_input

        # 7. Execute the tool
        tool_output = tool_registry.call(tool_name, **args)

        # 8. Synthesize and return the response
        return synthesize_response(tool_output)

    except Exception as e:
        error_message = f"An error occurred during processing: {e}"
        return synthesize_response(error_message)

# --- 4. Main Agent Loop ---
def main():
    """The main interactive loop for Agent V11."""
    print(f"=== {persona_config.get('name', 'Agent V11')} started. Type 'exit' to quit. ===")
    
    while True:
        try:
            user_input = input(">> ")
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            print("Agent: Processing...")
            response = run_orchestration(user_input)
            print(f"Agent: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()