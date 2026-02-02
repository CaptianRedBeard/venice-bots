import json

class SimpleOrchestrator:
    def __init__(self, llm_client, tool_registry):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
    
    def plan_and_execute(self, user_input):
        """Plan and execute a sequence of tool calls to answer the user's request.
        
        Args:
            user_input (str): The user's request
            
        Returns:
            str: Final summarized answer from the LLM
        """
        # Step 1: Create planner prompt and get the plan
        plan = self._create_plan(user_input)
        
        # Step 2: Execute the plan
        execution_results = self._execute_plan(plan)
        
        # Step 3: Generate final response
        final_response = self._generate_final_response(user_input, execution_results)
        
        return final_response
    
    def _create_plan(self, user_input):
        """Create a plan by asking the LLM to analyze the request and available tools."""
        tools_prompt = self.tool_registry.get_tools_for_prompt()
        
        planner_prompt = f"""You are an AI planner that analyzes user requests and creates a plan using available tools.

Available tools:
{tools_prompt}

Your task: Analyze the user's request and create a JSON plan with the following structure:
{{"plan": [{{"tool_name": "function_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}, ...]}}

Rules:
- Output ONLY valid JSON, no other text
- For tools with no arguments, use an empty object: {{"arguments": {{}}}}
- Use the exact tool names from the list above
- Be specific with argument values based on the user request
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
            
            # Extract and parse JSON
            json_response = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response in case there's extra text
            json_start = json_response.find('{')
            json_end = json_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = json_response[json_start:json_end]
                plan_data = json.loads(json_text)
                return plan_data.get("plan", [])
            else:
                raise ValueError("No JSON found in response")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse plan JSON: {e}. Response was: {json_response}")
        except Exception as e:
            raise ValueError(f"Error creating plan: {e}")
    
    def _execute_plan(self, plan):
        """Execute the plan by calling tools in sequence."""
        execution_results = []
        
        for i, step in enumerate(plan):
            tool_name = step.get("tool_name")
            arguments = step.get("arguments", {})
            
            try:
                # Convert string arguments to appropriate types
                processed_args = {}
                for key, value in arguments.items():
                    if isinstance(value, str):
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
                
            except Exception as e:
                execution_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": f"Error: {str(e)}",
                    "success": False
                })
        
        return execution_results
    
    def _generate_final_response(self, user_input, execution_results):
        """Generate a final conversational response based on execution results."""
        # Format execution results for the prompt
        results_text = "\n".join([
            f"Step {result['step']}: Called {result['tool']}({result['arguments']}) -> {result['result']}"
            for result in execution_results
        ])
        
        summarizer_prompt = f"""You are a helpful AI assistant. Based on the user's original request and the tool execution results below, provide a conversational, helpful response.

Original user request: {user_input}

Tool execution results:
{results_text}

Provide a natural, conversational response that directly answers the user's question based on these results. Be helpful and clear."""

        try:
            response = self.llm_client.chat.completions.create(
                model="venice-uncensored",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides natural conversational responses based on tool execution results."},
                    {"role": "user", "content": summarizer_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I encountered an error while generating my response: {str(e)}"