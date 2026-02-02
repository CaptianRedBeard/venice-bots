import json
from typing import List, Dict, Optional
from .knowledge_base import KnowledgeBase

class MemoryManager:
    def __init__(self, requesting_persona: str, llm_client):
        self.requesting_persona = requesting_persona
        self.llm_client = llm_client
    
    def deep_churn(self, target_facts: List[str], target_persona: str):
        """Process staging facts and integrate them into stable memory for a target persona."""
        try:
            # Step A: Instantiate KnowledgeBase for target persona
            kb = KnowledgeBase(persona_name=target_persona)
            
            # Step B: Get facts from target and user personas for hierarchy
            stable_facts_target = kb.get_all_facts()
            
            # Get user persona facts as source of truth
            user_kb = KnowledgeBase(persona_name="user")
            stable_facts_user = user_kb.get_all_facts()
            
            if not target_facts:
                # Nothing to process
                return
            
            # Step C: Process each new fact
            for new_fact in target_facts:
                try:
                    action_decision = self._resolve_fact_conflict(new_fact, stable_facts_target, stable_facts_user, target_persona)
                    if not action_decision:
                        # Failed to get decision, skip this fact
                        continue
                    
                    action = action_decision.get("action", "IGNORE")
                    target_fact = action_decision.get("target_fact", "")
                    
                    # Step D: Execute action with ACL checking
                    if action == "APPEND":
                        try:
                            kb.store_fact(new_fact)
                        except PermissionError:
                            print(f"Permission denied: {self.requesting_persona} cannot write to {target_persona}")
                    elif action == "UPDATE":
                        if target_fact:
                            try:
                                kb.update_fact(target_fact, new_fact)
                            except PermissionError:
                                print(f"Permission denied: {self.requesting_persona} cannot write to {target_persona}")
                    # IGNORE: do nothing
                    
                except Exception as e:
                    # Error processing individual fact, continue with others
                    print(f"Error processing fact '{new_fact}': {e}")
                    continue
            
            # Step E: Clear staging for target persona
            kb.clear_staging()
            
        except Exception as e:
            print(f"Error during deep churn: {e}")
    
    def _resolve_fact_conflict(self, new_fact: str, target_facts: List[str], user_facts: List[str], target_persona: str) -> Optional[Dict]:
        """Use LLM to determine action for a new fact with source of truth hierarchy."""
        target_facts_text = "\n".join([f"- {fact}" for fact in target_facts]) if target_facts else "No existing facts."
        user_facts_text = "\n".join([f"- {fact}" for fact in user_facts]) if user_facts else "No existing facts."
        
        prompt = f"""You are a knowledge adjudicator. Here is a new fact to integrate: "{new_fact}".

Here are the facts already known by the target persona ('{target_persona}'):
{target_facts_text}

Crucially, here are the facts known by the 'user' persona, which is the higher-priority source of truth:
{user_facts_text}

Based on all this information, decide what action to perform on the target persona's memory:

Determine the appropriate action:
- APPEND: Add the new fact as a separate entry (no conflicts or new information)
- UPDATE: Replace an existing fact with the new fact (contradictory information or more detailed version)
- IGNORE: Do not add the fact (duplicate or irrelevant, especially if user persona already has this information)

Respond with ONLY valid JSON:
{{"action": "APPEND|UPDATE|IGNORE", "target_fact": "exact_fact_to_update_if_action_is_UPDATE"}}

Rules:
- If action is UPDATE, include the exact fact to replace in target_fact
- If action is APPEND or IGNORE, target_fact can be empty string
- Consider semantic similarity, not just exact matching
- Prefer updating over appending when facts are about the same entity/property
- If user persona already knows this fact, consider IGNORE (avoid duplication)
- Source of truth hierarchy: user facts > target persona facts

JSON:"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="venice-uncensored",
                messages=[
                    {"role": "system", "content": "You are a precise knowledge adjudicator that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            json_response = response.choices[0].message.content.strip()
            json_start = json_response.find('{')
            json_end = json_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = json_response[json_start:json_end]
                decision = json.loads(json_text)
                
                # Validate action
                valid_actions = ["APPEND", "UPDATE", "IGNORE"]
                if decision.get("action") not in valid_actions:
                    return None
                
                return decision
            else:
                return None
                
        except Exception:
            return None
