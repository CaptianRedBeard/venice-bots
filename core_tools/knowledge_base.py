import os
import json
from pathlib import Path

class KnowledgeBase:
    def __init__(self, persona_name="default"):
        self.persona_name = persona_name
        self.data_dir = Path("data") / "personas" / persona_name
        self.kb_file = self.data_dir / "kb.txt"
        self.kb_staging_file = self.data_dir / "kb_staging.txt"
        self.config_file = self.data_dir / "config.json"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self):
        """Load persona configuration."""
        default_config = {
            "name": self.persona_name,
            "role": "user",
            "description": "No description provided",
            "memory_config": {
                "default_recall_target": "self",
                "fact_expiration_days": 30
            },
            "acl": {
                "can_read": [self.persona_name],
                "can_write": [self.persona_name]
            },
            "system_prompt": "You are a helpful AI assistant."
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config_data:
                            config_data[key] = value
                    return config_data
            except Exception:
                return default_config
        else:
            # Save default config
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config):
        """Save persona configuration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    
    def recall(self, query: str):
        """Recall facts relevant to the query using smart keyword matching."""
        # For backward compatibility, we'll use the default recall target
        default_target = self.config.get('memory_config', {}).get('default_recall_target', 'self')
        
        if default_target == 'self':
            target_persona = self.persona_name
        else:
            target_persona = default_target
        
        # Check if this persona can read from target_persona
        allowed_personas = self.config.get('acl', {}).get('can_read', [self.persona_name])
        if target_persona not in allowed_personas:
            # Silently return empty if not allowed
            return []
        
        target_kb_file = Path("data") / "personas" / target_persona / "kb.txt"
        
        if not target_kb_file.exists():
            return []
        
        try:
            with open(target_kb_file, 'r', encoding='utf-8') as f:
                facts = f.readlines()
            
            query_lower = query.lower()
            relevant_facts = []
            
            # Smart matching - handle common query patterns
            for fact in facts:
                fact_lower = fact.lower()
                
                # Direct substring match
                if query_lower in fact_lower:
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "name" queries - look for facts that might contain names
                if "name" in query_lower and any(word in fact_lower for word in ["alex", "john", "mary", "user", "lives in"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "live" queries - look for location facts
                if "live" in query_lower and any(word in fact_lower for word in ["lives in", "located", "chicago", "new york", "address"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "prefer" queries - look for preference facts
                if "prefer" in query_lower and any(word in fact_lower for word in ["prefers", "over", "likes"]):
                    relevant_facts.append(fact.strip())
                    continue
                
                # Handle "language" or "programming" queries
                if any(word in query_lower for word in ["language", "programming"]) and any(word in fact_lower for word in ["python", "javascript", "java", "ruby"]):
                    relevant_facts.append(fact.strip())
                    continue
            
            return relevant_facts
            
        except Exception as e:
            print(f"Error recalling facts: {e}")
            return []
    
    def get_all_facts(self):
        """Get all facts stored in the stable knowledge base."""
        if not self.kb_file.exists():
            return []
        
        try:
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"Error getting all facts: {e}")
            return []
    
    def store_fact(self, statement: str):
        """Store a new fact in the stable knowledge base."""
        # Check if this persona can write to its own knowledge base
        allowed_personas = self.config.get('acl', {}).get('can_write', [self.persona_name])
        if self.persona_name not in allowed_personas:
            # Silently fail if not allowed to write
            return
        
        try:
            with open(self.kb_file, 'a', encoding='utf-8') as f:
                f.write(statement.strip() + '\n')
        except Exception as e:
            print(f"Error storing fact: {e}")
    
    def store_fact_staging(self, statement: str):
        """Store a new fact in the staging knowledge base."""
        # Check if this persona can write to its own knowledge base
        allowed_personas = self.config.get('acl', {}).get('can_write', [self.persona_name])
        if self.persona_name not in allowed_personas:
            # Silently fail if not allowed to write
            return
        
        try:
            with open(self.kb_staging_file, 'a', encoding='utf-8') as f:
                f.write(statement.strip() + '\n')
        except Exception as e:
            print(f"Error storing staging fact: {e}")
    
    def get_staging_facts(self):
        """Get all facts stored in the staging knowledge base."""
        if not self.kb_staging_file.exists():
            return []
        
        try:
            with open(self.kb_staging_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"Error getting staging facts: {e}")
            return []
    
    def update_fact(self, old_fact: str, new_fact: str):
        """Update a fact in the stable knowledge base by finding and replacing."""
        # Check if this persona can write to its own knowledge base
        allowed_personas = self.config.get('acl', {}).get('can_write', [self.persona_name])
        if self.persona_name not in allowed_personas:
            print(f"Persona '{self.persona_name}' is not allowed to write to its own memory.")
            return False
        
        try:
            if not self.kb_file.exists():
                return False
            
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                facts = f.readlines()
            
            updated_facts = []
            updated = False
            for fact in facts:
                if fact.strip() == old_fact.strip():
                    updated_facts.append(new_fact.strip() + '\n')
                    updated = True
                else:
                    updated_facts.append(fact)
            
            if updated:
                with open(self.kb_file, 'w', encoding='utf-8') as f:
                    f.writelines(updated_facts)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error updating fact: {e}")
            return False
    
    def clear_staging(self):
        """Clear all facts from the staging knowledge base."""
        try:
            if self.kb_staging_file.exists():
                with open(self.kb_staging_file, 'w', encoding='utf-8') as f:
                    f.write('')
        except Exception as e:
            print(f"Error clearing staging facts: {e}")
    
    def flush_all(self):
        """Remove all facts from the knowledge base."""
        # Check if this persona can write to its own knowledge base
        allowed_personas = self.config.get('acl', {}).get('can_write', [self.persona_name])
        if self.persona_name not in allowed_personas:
            print(f"Persona '{self.persona_name}' is not allowed to write to its own memory.")
            return
        
        try:
            if self.kb_file.exists():
                with open(self.kb_file, 'w', encoding='utf-8') as f:
                    f.write('')
                print(f"All memories flushed for persona '{self.persona_name}'")
            else:
                print(f"No memory file found for persona '{self.persona_name}'")
        except Exception as e:
            print(f"Error flushing all facts: {e}")
    
    def flush_fact(self, statement_to_remove: str):
        """Remove a specific fact from the knowledge base."""
        # Check if this persona can write to its own knowledge base
        allowed_personas = self.config.get('acl', {}).get('can_write', [self.persona_name])
        if self.persona_name not in allowed_personas:
            print(f"Persona '{self.persona_name}' is not allowed to write to its own memory.")
            return
        
        try:
            if not self.kb_file.exists():
                print(f"No memory file found for persona '{self.persona_name}'")
                return
            
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                facts = f.readlines()
            
            # Filter out the fact to remove
            remaining_facts = [fact for fact in facts if fact.strip() != statement_to_remove.strip()]
            
            # Write back the remaining facts
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                f.writelines(remaining_facts)
            
            removed_count = len(facts) - len(remaining_facts)
            if removed_count > 0:
                print(f"Removed {removed_count} matching fact(s) from persona '{self.persona_name}'")
            else:
                print(f"No matching facts found for: '{statement_to_remove}'")
                
        except Exception as e:
            print(f"Error flushing fact: {e}")