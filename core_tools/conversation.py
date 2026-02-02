try:
    import tiktoken
except ImportError:
    raise ImportError(
        "tiktoken library not found. Install with: pip install tiktoken"
    )

class ConversationHistory:
    def __init__(self, max_tokens=None, max_messages=None):
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.history = []
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def _count_tokens(self, messages):
        """Count tokens in a list of messages."""
        if not messages:
            return 0
        
        # Count tokens in all message content
        text = ""
        for msg in messages:
            text += msg.get('content', '')
        
        return len(self.encoding.encode(text))
    
    def _trim_history(self):
        """Trim history based on token and message limits."""
        if not self.history:
            return
        
        # Preserve system message if it exists
        system_msg = None
        if self.history and self.history[0].get('role') == 'system':
            system_msg = self.history.pop(0)
        
        # Trim by message limit
        if self.max_messages and len(self.history) > self.max_messages:
            # Remove oldest messages
            excess = len(self.history) - self.max_messages
            self.history = self.history[excess:]
        
        # Trim by token limit
        if self.max_tokens:
            while self._count_tokens(self.history) > self.max_tokens and self.history:
                # Remove oldest message
                self.history.pop(0)
        
        # Restore system message if it existed
        if system_msg:
            self.history.insert(0, system_msg)
    
    def add_message(self, role, content):
        """Add a new message to the conversation history."""
        self.history.append({'role': role, 'content': content})
        self._trim_history()
    
    def get_history(self):
        """Return the current conversation history."""
        return self.history.copy()