import json
from pathlib import Path

# Import the KnowledgeBase class from our module
try:
    from .knowledge_base import KnowledgeBase
except ImportError:
    # Fallback for when the module is run directly
    from knowledge_base import KnowledgeBase

class CognitiveOrchestrator:
    def __init__(self, llm_client, tool_registry, persona_name="venice_assistant"):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.persona_name = persona_name
        self.knowledge_base = KnowledgeBase(persona_name=persona_name)
        self.turn_count = 0
    
    def plan_and_execute(self, user_input: str):
        """Execute the four-stage cognitive workflow: Recall, Plan, Execute & Summarize, Memorize."""
        
        # Increment turn counter
        self.turn_count += 1
        
        # Stage 1: Recall
        recalled_facts = self._recall(user_input)
        
        # Stage 2: Plan
        plan = self._plan(user_input, recalled_facts)
        
        # Stage 3: Execute & Summarize
        execution_results = self._execute_plan(plan)
        final_response = self._summarize(user_input, execution_results, recalled_facts)
        
        # Stage 4: Memorize
        self._memorize(user_input, final_response)
        
        return final_response
    
    def _recall(self, user_input):
        """Recall relevant facts from both user and assistant knowledge bases."""
        all_facts = []
        recall_errors = []
        
        # Always check user persona for personal information
        try:
            user_kb = KnowledgeBase(persona_name="user")
            user_facts = self._search_facts_in_kb(user_input, user_kb, "user")
            all_facts.extend(user_facts)
            
            if not user_facts:
                recall_errors.append(f"No user facts found (or no permission to read user persona)")
                
        except Exception as e:
            error_msg = f"Error recalling from user persona: {e}"
            recall_errors.append(error_msg)
            print(f"⚠️  RECALL ERROR: {error_msg}")
        
        # Also check current persona for its own knowledge
        try:
            persona_facts = self._search_facts_in_kb(user_input, self.knowledge_base, self.persona_name)
            all_facts.extend(persona_facts)
            
            if not persona_facts:
                recall_errors.append(f"No {self.persona_name} facts found")
                
        except Exception as e:
            error_msg = f"Error recalling from {self.persona_name} persona: {e}"
            recall_errors.append(error_msg)
            print(f"⚠️  RECALL ERROR: {error_msg}")
        
        # Debug permission issues if no facts were found
        if not all_facts and recall_errors:
            self._debug_permission_issue(recall_errors)
        
        return all_facts
    
    def _debug_permission_issue(self, errors):
        """Debug permission issues when recall fails."""
        print(f"\n🔍 DEBUGGING RECALL FAILURE for persona '{self.persona_name}':")
        print(f"   Errors: {errors}")
        
        try:
            # Check current persona's ACL
            current_acl = self.knowledge_base.config.get('acl', {})
            current_can_read = current_acl.get('can_read', [])
            print(f"   {self.persona_name} can_read: {current_can_read}")
            
            # Check user persona's ACL if it exists
            user_persona_path = Path("data/personas/user/config.json")
            if user_persona_path.exists():
                with open(user_persona_path, 'r') as f:
                    user_config = json.load(f)
                user_acl = user_config.get('acl', {})
                user_can_read = user_acl.get('can_read', [])
                print(f"   user can_read: {user_can_read}")
                
                # Check if current persona has permission
                if self.persona_name not in user_can_read:
                    print(f"   ❌ PERMISSION ISSUE: '{self.persona_name}' not in user can_read list!")
                    print(f"   💡 FIX: Add '{self.persona_name}' to user persona's can_read ACL")
                else:
                    print(f"   ✅ Permission check passed for user access")
            else:
                print(f"   ⚠️  User persona does not exist")
                
        except Exception as e:
            print(f"   Error debugging permissions: {e}")
        
        print()
    
    def _search_facts_in_kb(self, query: str, kb, persona_name):
        """Search for relevant facts in a specific knowledge base."""
        # Check if this persona can read from the target
        allowed_personas = kb.config.get('acl', {}).get('can_read', [self.persona_name])
        if self.persona_name not in allowed_personas:
            raise PermissionError(f"Persona '{self.persona_name}' not allowed to read from '{persona_name}'. "
                                f"Allowed: {allowed_personas}")
        
        target_kb_file = Path("data") / "personas" / persona_name / "kb.txt"
        
        if not target_kb_file.exists():
            return []
        
        try:
            with open(target_kb_file, 'r', encoding='utf-8') as f:
                facts = f.readlines()
            
            if not facts:
                return []
            
            query_lower = query.lower()
            relevant_facts = []
            
            # Smart matching - handle common query patterns
            for fact in facts:
                fact_lower = fact.lower()
                
                # Direct substring match
                if query_lower in fact_lower:
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "what do you know about me" queries - return all user facts
                if any(phrase in query_lower for phrase in ["what do you know about me", "tell me about myself", "who am i", "my information"]):
                    if persona_name == "user":
                        relevant_facts.append(fact.strip())
                        continue
                
                # Handle "what did we discuss" queries - return all assistant facts
                if any(phrase in query_lower for phrase in ["what did we discuss", "what did we talk about", "earlier conversation", "previous conversation"]):
                    if persona_name != "user":
                        relevant_facts.append(fact.strip())
                        continue
                
                # Handle "name" queries - look for facts that might contain names
                if "name" in query_lower and any(word in fact_lower for word in ["name is", "called", "goes by"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "live" queries - look for location facts
                if "live" in query_lower and any(word in fact_lower for word in ["lives in", "based in", "located"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "work" or "job" queries
                if any(word in query_lower for word in ["work", "job", "career"]) and any(word in fact_lower for word in ["software engineer", "techcorp", "startup"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "hobby" or "interest" queries
                if any(word in query_lower for word in ["hobby", "interest", "enjoy", "prefer", "hobbies", "activities", "fun"]) and any(word in fact_lower for word in ["hiking", "photography", "guitar", "movies", "playing", "nature", "trails"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "hiking" specific queries
                if "hiking" in query_lower and any(word in fact_lower for word in ["hiking", "trail", "groups", "forums"]):
                    relevant_facts.append(fact.strip())
                    continue
            
            # NEW: Fallback for general queries - return recent facts if no specific matches
            if not relevant_facts:
                general_query_patterns = [
                    "tell me about", "what do we have", "world so far", "summarize", 
                    "what have we", "what have you", "reminder", "refresh", "catch up"
                ]
                
                if any(phrase in query_lower for phrase in general_query_patterns):
                    # Return the most recent facts as general context
                    recent_count = min(5, len(facts))  # Get up to 5 most recent facts
                    relevant_facts = [fact.strip() for fact in facts[-recent_count:]]
                    print(f"📝 FALLBACK: Using {len(relevant_facts)} recent facts for general query")
            
            return relevant_facts
            
        except Exception as e:
            print(f"Error recalling facts: {e}")
            return []
    
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

Rules:
- Output ONLY valid JSON, no other text
- For tools with no arguments, use an empty object: {{"arguments": {{}}}}
- Use the exact tool names from the list above
- Be specific with argument values based on the user request
- Consider the recalled facts when planning - if you already know the answer from facts, you may not need tools
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
        """Execute the plan by calling tools in sequence."""
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
                
            except Exception as e:
                execution_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": f"Error: {str(e)}",
                    "success": False
                })
        
        return execution_results
    
    def _summarize(self, user_input, execution_results, recalled_facts):
        """Generate a final response using execution results and recalled facts."""
        results_text = "\n".join([
            f"Step {result['step']}: Called {result['tool']}({result['arguments']}) -> {result['result']}"
            for result in execution_results
        ])
        
        facts_text = "\n".join([f"- {fact}" for fact in recalled_facts]) if recalled_facts else "No relevant facts recalled."
        
        summarizer_prompt = f"""You are a helpful AI assistant with memory. Based on the user's request, your recalled knowledge, and tool execution results, provide a conversational, helpful response.

Original user request: {user_input}

Recalled knowledge from previous conversations:
{facts_text}

Tool execution results:
{results_text}

Provide a natural, conversational response that incorporates both your recalled knowledge and the tool results. Be helpful and build upon what you remember. If you already know the answer from recalled facts, use that knowledge directly."""

        try:
            response = self.llm_client.chat.completions.create(
                model="venice-uncensored",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant with memory that provides natural responses based on knowledge and tool results."},
                    {"role": "user", "content": summarizer_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I encountered an error while generating my response: {str(e)}"
    
    def _memorize(self, user_input, final_response):
        """Extract and store new facts from the conversation - Persona-agnostic routing."""
        memorize_prompt = f"""Extract durable, declarative facts from this conversation. Return a JSON object with a list of memories.

User: {user_input}
Assistant: {final_response}

Current persona: {self.persona_name}

For each fact you extract, determine the most appropriate target persona:
- "user": For personal information about the user (preferences, personal details, private information, requirements)
- "{self.persona_name}": For information related to this persona's domain and expertise
- "venice_assistant": For general conversational context and meta-information

Rules:
- Extract facts that might be useful in future conversations
- Make facts self-contained and clear
- Route user-specific information to the "user" persona
- Route domain-specific information to the current persona ("{self.persona_name}")
- Route general conversation details to "venice_assistant"

Output format:
{{
  "memories": [
    {{
      "statement": "User prefers dark fantasy themes for their TTRPG world.",
      "target_persona": "user"
    }},
    {{
      "statement": "The world Umbralys features eternal twilight and shadow magic.",
      "target_persona": "{self.persona_name}"
    }}
  ]
}}"""

        try:
            response = self.llm_client.chat.completions.create(
                model="venice-uncensored",
                messages=[
                    {"role": "system", "content": "You extract facts from conversations and determine routing to personas in JSON format."},
                    {"role": "user", "content": memorize_prompt}
                ],
                temperature=0.3
            )
            
            json_response = response.choices[0].message.content.strip()
            json_start = json_response.find('{')
            json_end = json_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = json_response[json_start:json_end]
                memory_data = json.loads(json_text)
                
                if isinstance(memory_data, dict) and "memories" in memory_data:
                    memories = memory_data["memories"]
                    
                    if isinstance(memories, list):
                        for memory in memories:
                            if isinstance(memory, dict):
                                statement = memory.get("statement")
                                target_persona = memory.get("target_persona")
                                
                                if statement and target_persona:
                                    # Import here to avoid circular imports
                                    from .memory_manager import MemoryManager
                                    memory_manager = MemoryManager(self.persona_name, self.llm_client)
                                    memory_manager.deep_churn([statement], target_persona)
                    
                    # Check if it's time for general churn on the persona's own memory
                    churn_interval = self.knowledge_base.config.get("memory_config", {}).get("memory_churn_interval", 3)
                    if self.turn_count % churn_interval == 0:
                        memory_manager = MemoryManager(self.persona_name, self.llm_client)
                        # Process any remaining facts in persona's staging
                        kb = KnowledgeBase(self.persona_name)
                        staging_facts = kb.get_staging_facts()
                        if staging_facts:
                            memory_manager.deep_churn(staging_facts, self.persona_name)
                            
        except Exception as e:
            print(f"⚠️  MEMORY ERROR: {e}")
