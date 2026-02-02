from core_tools.config import get_venice_client

def generate_description(subject: str, style: str = "detailed"):
    """Generate creative descriptions for characters, locations, or objects.
    
    Args:
        subject (str): What to generate a description for
        style (str): Style of description (detailed, poetic, mysterious, etc.)
        
    Returns:
        str: Creative description of the subject
    """
    llm_client = get_venice_client()
    prompt = f"Generate a {style} description for: {subject}. Make it evocative and engaging."
    
    try:
        response = llm_client.chat.completions.create(
            model="venice-uncensored",
            messages=[
                {"role": "system", "content": "You are a creative writer that brings subjects to life with vivid descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating description: {str(e)}"

def expand_concept(concept: str, focus: str = "general"):
    """Expand on a concept with additional details, history, or implications.
    
    Args:
        concept (str): The concept to expand upon
        focus (str): What aspect to focus on (history, mechanics, implications, etc.)
        
    Returns:
        str: Expanded details about the concept
    """
    llm_client = get_venice_client()
    prompt = f"Expand on the concept of '{concept}' with a focus on {focus}. Provide depth and interesting details."
    
    try:
        response = llm_client.chat.completions.create(
            model="venice-uncensored",
            messages=[
                {"role": "system", "content": "You are a creative world-builder that adds depth and consistency to concepts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error expanding concept: {str(e)}"
