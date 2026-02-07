import re

class IntentClassifier:
    """
    A deterministic classifier to map user intent to a primary tool.
    This component replaces the unreliable LLM-based planner.
    It can be extended by passing additional intents during initialization.
    """
    def __init__(self, extra_intents: dict = None):
        # Define keywords for each intent
        self.intent_map = {
            "find_files": ["find", "search", "list files", "find all", "search for", "list all"],
            "read_file": ["read", "show", "analyze", "what's in", "contents of", "open", "file"],
            "list_directory": ["what's in directory", "list directory", "dir", "ls"],
            # --- ADD JOURNALING INTENTS ---
            "append_to_section": [
                "add to", "add", "log", "note", "note down", "record", "update", "append"
            ],
            "create_entry_from_template": [
                "create entry", "new entry", "start a new", "create daily", "create weekly"
            ]
        }

        # If extra intents are provided, merge them into the map
        if extra_intents:
            for tool_name, keywords in extra_intents.items():
                if tool_name in self.intent_map:
                    self.intent_map[tool_name].extend(keywords)
                else:
                    self.intent_map[tool_name] = keywords

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
        # We check our new, more specific intents first
        if any(phrase in normalized_input for phrase in self.intent_map.get("create_entry_from_template", [])):
            return "create_entry_from_template"
        if any(phrase in normalized_input for phrase in self.intent_map.get("append_to_section", [])):
            return "append_to_section"

        # Then check the original file system intents
        if any(phrase in normalized_input for phrase in self.intent_map.get("list_directory", [])):
            return "list_directory"
        if any(phrase in normalized_input for phrase in self.intent_map.get("read_file", [])):
            return "read_file"
        if any(phrase in normalized_input for phrase in self.intent_map.get("find_files", [])):
            return "find_files"

        return "unknown"