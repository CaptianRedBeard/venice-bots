#!/usr/bin/env python3
"""
Agent V09: The Code Analyst (Stateless Tool User)
A stateless agent for analyzing Python project structure and functionality.
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
    # Import the new tool functions and custom exceptions
    from core_tools.file_system_tool import (
        read_file,
        list_directory,
        find_files,
        FileSystemToolError,
        FileNotFoundError,
        PathTraversalError,
        NotADirectoryError
    )
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class StatelessCognitiveOrchestrator(CognitiveOrchestrator):
    """
    A modified CognitiveOrchestrator that bypasses the memory system
    for stateless, task-oriented interactions.
    """

    def plan_and_execute(self, user_input: str):
        """
        Execute a simplified three-stage cognitive workflow: Plan, Execute & Summarize.
        The Recall and Memorize stages are disabled.
        """
        # Stage 1: Plan (using no recalled context)
        plan = self._plan(user_input, recalled_facts=[])
        
        # Stage 2: Execute & Summarize
        execution_results = self._execute_plan(plan)
        final_response = self._summarize(user_input, execution_results, recalled_facts=[])
        
        return final_response

    def _plan(self, user_input, recalled_facts):
        """Create a plan using LLM with context from recalled facts."""
        tools_prompt = self.tool_registry.get_tools_for_prompt()
        facts_prompt = "\n".join([f"- {fact}" for fact in recalled_facts]) if recalled_facts else "No relevant facts recalled."
        
        planner_prompt = f"""You are an AI planner that analyzes user requests and creates a plan using available tools and recalled knowledge.
        Available tools:
        {tools_prompt}
        
        Recalled facts from knowledge base:
        {facts_prompt}
        
        Your task: Analyze the user's request and create a JSON plan with the following structure:
        {{"plan": [{{"tool_name": "function_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}, ...]}}
        
        CRITICAL RULES FOR PATH ARGUMENTS:
        - NEVER use absolute paths (e.g., /home/user/project). All paths must be relative.
        - To refer to the project root directory, use the single dot '.'.
        - If the user asks for "the entire project" or "the whole project", use '.' for the root_path.
        - If the user asks for "the X directory", assume the path is 'X' unless they provide a more specific path.
        
        General Rules:
        - Output ONLY valid JSON, no other text
        - For tools with no arguments, use an empty object: {{"arguments": {{}}}}
        - Use the exact tool names from the list above
        - Be specific with argument values based on the user request
        - Consider the recalled facts when planning
        - if you already know the answer from facts, you may not need tools
        - Create a logical sequence of steps if multiple tools are needed
        
        User request: {user_input}
        JSON plan:"""
        try:
            response = self.llm_client.chat.completions.create(
                model="venice-uncensored",
                messages=[
                    {"role": "system", "content": "You are a precise planner that outputs only valid JSON."},
                    {"role": "user", "content": planner_prompt}
                ],
                temperature=0.1
            )
            json_response = response.choices[0].message.content.strip()
            json_start = json_response.find('{')
            json_end = json_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_text = json_response[json_start:json_end]
                plan_data = json.loads(json_text)
                return plan_data.get("plan", [])
            else:
                return []
        except Exception:
            return []

    def _execute_plan(self, plan):
        """
        Execute the plan by calling tools in sequence.
        This version is updated to handle custom FileSystemToolError exceptions.
        """
        execution_results = []
        for i, step in enumerate(plan):
            tool_name = step.get("tool_name")
            arguments = step.get("arguments", {})
            try:
                processed_args = {}
                for key, value in arguments.items():
                    if isinstance(value, str):
                        try:
                            if '.' in value and value.replace('.', '').replace('-', '').isdigit():
                                processed_args[key] = float(value)
                            elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                                processed_args[key] = int(value)
                            else:
                                processed_args[key] = value
                        except (ValueError, AttributeError):
                            processed_args[key] = value
                    else:
                        processed_args[key] = value
                
                result = self.tool_registry.call_tool(tool_name, **processed_args)
                execution_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "success": True
                })
            except FileSystemToolError as e:
                # Catch our custom file system errors and report them cleanly
                execution_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": f"A file system error occurred: {str(e)}",
                    "success": False
                })
            except Exception as e:
                # Catch any other unexpected errors
                execution_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": f"An unexpected error occurred: {str(e)}",
                    "success": False
                })
        return execution_results


def main():
    print("=== Agent V09 - The Code Analyst (Stateless) ===")

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

    # Initialize knowledge base with persona configuration
    try:
        persona_name = "code_analyst"
        knowledge_base = KnowledgeBase(persona_name)
        print(f"✓ Knowledge base initialized (persona: {persona_name})")
        print(f"✓ Description: {knowledge_base.config.get('description', 'No description')}")
        # Note: Memory system is disabled in the orchestrator for this agent
    except Exception as e:
        print(f"✗ Failed to load persona configuration: {e}")
        sys.exit(1)

    # Initialize the stateless cognitive orchestrator
    orchestrator = StatelessCognitiveOrchestrator(client, tool_registry, persona_name=persona_name)
    print("✓ Stateless Cognitive Orchestrator initialized")
    print(f"✓ System prompt loaded: {knowledge_base.config.get('system_prompt', 'No system prompt')[0:50]}...")

    print(f"\nAgent V09 The Code Analyst started. Type 'exit' to quit.")
    print(f"This agent is stateless and will not remember previous interactions.")
    print()

    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if not user_input:
                continue

            # Use the stateless orchestrator to process the request
            print("Agent: Analyzing...")
            final_response = orchestrator.plan_and_execute(user_input)
            print(f"Agent: {final_response}\n")

        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during processing: {e}")

if __name__ == "__main__":
    main()