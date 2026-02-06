import re

class IntentClassifier:
    """
    A deterministic classifier to map user intent to a primary tool.
    This component replaces the unreliable LLM-based planner.
    """
    def __init__(self):
        # Define keywords for each intent
        self.intent_map = {
            "find_files": ["find", "search", "list files", "find all", "search for", "list all"],
            "read_file": ["read", "show", "analyze", "what's in", "contents of", "open", "file"],
            "list_directory": ["what's in directory", "list directory", "dir", "ls"]
        }

    def classify(self, user_input: str) -> str:
        """
        Classifies user input to determine the primary tool to use.
        
        Args:
            user_input (str): The raw string input from the user.
            
        Returns:
            str: The name of the tool to invoke (e.g., "find_files").
                 Returns "unknown" if no intent matches.
        """
        if not isinstance(user_input, str):
            return "unknown"
            
        # Normalize input for case-insensitive matching
        normalized_input = user_input.lower()

        # Check for intents, prioritizing more specific phrases first
        if any(phrase in normalized_input for phrase in self.intent_map["list_directory"]):
            return "list_directory"
        
        if any(phrase in normalized_input for phrase in self.intent_map["read_file"]):
            return "read_file"

        if any(phrase in normalized_input for phrase in self.intent_map["find_files"]):
            return "find_files"

        return "unknown"