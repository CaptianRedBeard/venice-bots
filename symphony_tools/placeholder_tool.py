from symphony.tool import SymphonyTool

class AnswerQuestionTool(SymphonyTool):
    """A tool for the agent to provide a final answer to the user's question based on the provided context."""
    
    @property
    def name(self) -> str:
        return "answer_question"

    @property
    def description(self) -> str:
        return "Use this tool to provide the final answer to the user's question after you have reviewed the provided context."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The complete and final answer to the user's question, based only on the provided context."
                }
            },
            "required": ["answer"]
        }

    def to_openai_schema(self) -> dict:
        """Returns the OpenAI function-calling schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters(),
            },
        }

    def run(self, answer: str) -> str:
        """Returns the final answer."""
        return answer