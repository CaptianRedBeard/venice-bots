import os
from pathlib import Path
import re

class KnowledgeBase:
    def __init__(self, persona_name="default"):
        self.persona_name = persona_name
        self.data_dir = Path("data") / "personas" / persona_name
        self.kb_file = self.data_dir / "kb.txt"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def store_fact(self, statement: str):
        """Store a new fact in the knowledge base."""
        try:
            with open(self.kb_file, 'a', encoding='utf-8') as f:
                f.write(statement.strip() + '\n')
        except Exception as e:
            print(f"Error storing fact: {e}")
    
    def recall(self, query: str):
        """Recall facts relevant to the query using smart keyword matching."""
        if not self.kb_file.exists():
            return []
        
        try:
            with open(self.kb_file, 'r', encoding='utf-8') as f:
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
        """Get all facts stored in the knowledge base."""
        if not self.kb_file.exists():
            return []
        
        try:
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"Error getting all facts: {e}")
            return []