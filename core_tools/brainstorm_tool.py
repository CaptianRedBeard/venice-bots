from core_tools.config import get_venice_client

def brainstorm(topic: str, num_ideas: int = 3):
    """Generate creative ideas for any given topic.
    
    Args:
        topic (str): The topic to brainstorm ideas for
        num_ideas (int): Number of ideas to generate (default: 3)
        
    Returns:
        str: Creative ideas presented as a numbered list
    """
    llm_client = get_venice_client()
    prompt = f"Brainstorm {num_ideas} creative ideas related to: {topic}. Present them as a numbered list with brief descriptions."
    
    try:
        response = llm_client.chat.completions.create(
            model="venice-uncensored",
            messages=[
                {"role": "system", "content": "You are a creative brainstorming assistant that generates diverse, innovative ideas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating ideas: {str(e)}"
