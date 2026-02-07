from .config import get_venice_client, get_model_for_role
from .exceptions import ToolError
from .tool_registry import ToolRegistry

# --- JSON Schema for LLM Discovery ---
SUMMARIZE_SCHEMA = {
    "type": "function",
    "description": "Summarizes a given text into a few concise bullet points for a personal log.",
    "parameters": {
        "type": "object",
        "properties": {
            "text_to_summarize": {
                "type": "string",
                "description": "The full text that needs to be summarized."
            }
        },
        "required": ["text_to_summarize"]
    }
}

class SummarizerTool:
    """A tool to summarize text into a few concise bullet points."""
    def __init__(self, role: str = "reasoning"):
        self.client = get_venice_client()
        self.model = get_model_for_role(role)

    def summarize(self, text_to_summarize: str) -> str:
        """Summarizes the given text into a few concise bullet points."""
        if not text_to_summarize or not text_to_summarize.strip():
            return "Nothing to summarize."

        prompt = f"""Please summarize the following text into a few concise bullet points suitable for a personal log. The output should be only the bullet points, nothing else. Each bullet point should start with a hyphen (-).

        Text to summarize:
        "{text_to_summarize}"
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing text into concise bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise ToolError(f"Summarization failed: {e}")

# --- Helper function to initialize and register the tool ---
def initialize_and_register(tool_registry: ToolRegistry):
    """Initializes the SummarizerTool and registers its method."""
    instance = SummarizerTool()
    
    tool_registry.register(
        tool_name="summarize",
        tool_callable=instance.summarize,
        schema=SUMMARIZE_SCHEMA
    )
    return instance