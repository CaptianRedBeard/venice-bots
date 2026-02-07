import json
from .tool_registry import ToolRegistry
from .config import get_venice_client, get_model_for_role
from .exceptions import ToolError

class ToolFirstOrchestrator:
    """
    Orchestrates the "Tool Execution -> LLM Synthesis" workflow.
    This version is generic and includes dynamic header discovery.
    """
    def __init__(self, tool_registry: ToolRegistry, llm_client, llm_function_caller):
        """ Initializes the ToolFirstOrchestrator. """
        if not isinstance(tool_registry, ToolRegistry):
            raise TypeError("tool_registry must be an instance of ToolRegistry.")
        self.tool_registry = tool_registry
        self.llm_client = llm_client
        self.function_caller = llm_function_caller

    def _synthesize_response(self, tool_output: any, persona_config: dict) -> str:
        """Uses an LLM to synthesize the raw tool output into a user-friendly response."""
        system_prompt = persona_config.get('system_prompt', "You are a helpful assistant.")
        synthesis_prompt = f"""Summarize the following data for the user based on your persona. Do not add information that is not present in the data. If the data is an error message, report it clearly.
        
        Data: {json.dumps(tool_output, indent=2)}
        
        Summary:"""
        
        try:
            model = get_model_for_role('synthesis')
            response = self.llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": synthesis_prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"I was able to execute the tool, but I had trouble formatting the response. Here is the raw data:\n{tool_output}"

    def run(self, user_input: str, persona_config: dict) -> str:
        """Runs the enhanced workflow with smart features."""
        try:
            # 1. Check for summarization prompt
            if len(user_input) > 300:
                model = get_model_for_role('synthesis')
                response = self.llm_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. Respond only with 'yes' or 'no'."},
                        {"role": "user", "content": f"The user wants to add this note to their journal: '{user_input}'. Should I ask if they want to summarize it because it's long?"}
                    ],
                    temperature=0.1
                )
                if response.choices[0].message.content.strip().lower() == 'yes':
                    return "That's a long note. Should I log it as-is, or summarize it for you? (Reply with 'summarize' or 'log as-is')"

            # 2. Pre-emptively determine file_type and target_date for potential append operations
            file_type = 'daily'
            target_date = None
            # Use a lightweight LLM call to see if the user is asking to append and to what file
            intent_prompt = f"""
            Analyze the user's request: "{user_input}"
            Does the user want to add or log something? If so, determine if it's for a 'daily' or 'weekly' file and extract any date.
            If they are not asking to add or log, set file_type to 'none'.
            Respond ONLY with a JSON object: {{"file_type": "daily|weekly|none", "target_date": "YYYY-MM-DD|string|null"}}
            """
            model = get_model_for_role('reasoning')
            response = self.llm_client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": intent_prompt}], temperature=0.1
            )
            intent_result = json.loads(response.choices[0].message.content.strip())
            file_type = intent_result.get('file_type', 'daily')
            target_date = intent_result.get('target_date')

            # 3. Get headers if we think this is an append operation
            available_headers = []
            if file_type in ['daily', 'weekly']:
                try:
                    available_headers = self.tool_registry.call("get_headers", file_type=file_type, target_date_str=target_date)
                except ToolError:
                    # If the file doesn't exist or can't be read, we'll proceed without headers
                    pass

            # 4. Parse intent and arguments with the available headers
            all_schemas = self.tool_registry.get_all_schemas()
            tool_name, args = self.function_caller.parse(user_input, all_schemas, available_headers=available_headers)

            # 5. Handle user choice for summarization
            if tool_name == "unknown" and user_input.lower() in ["summarize", "log as-is"]:
                if not hasattr(self, '_pending_long_text'):
                    return "I don't have a previous long text to summarize or log. Please provide it again."
                
                if user_input.lower() == "summarize":
                    summarizer_tool = self.tool_registry.get("summarize")
                    summary = summarizer_tool.summarize(text_to_summarize=self._pending_long_text)
                    tool_name, args = self.function_caller.parse(f"Add '{summary}' to my journal.", all_schemas)
                    del self._pending_long_text
                elif user_input.lower() == "log as-is":
                    tool_name, args = self.function_caller.parse(self._pending_long_text, all_schemas)
                    del self._pending_long_text

            if tool_name == "unknown":
                persona_desc = persona_config.get('description', 'a helpful assistant')
                return f"I'm not sure how to handle that request. I am {persona_desc}."

            # 6. Store pending text if it's a long append request
            if len(user_input) > 300 and tool_name == "append_to_section":
                self._pending_long_text = user_input

            # 7. Execute the tool
            # If we determined a specific file_type/date, add it to the args for the init_hook
            if file_type in ['daily', 'weekly']:
                args['file_type'] = file_type
                if target_date:
                    args['target_date'] = target_date
            
            tool_output = self.tool_registry.call(tool_name, **args)

            # 8. Synthesize the response
            final_response = self._synthesize_response(tool_output, persona_config)
            return final_response

        except Exception as e:
            error_message = f"An error occurred during processing: {e}"
            return self._synthesize_response(error_message, persona_config)
        
        