import os
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    raise ImportError(
        "python-dotenv package not found. Install with: pip install python-dotenv"
    )

PROJECT_ROOT = Path(__file__).parent.parent

def load_env():
    """Load environment variables from .env file in project root."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        raise FileNotFoundError(
            f".env file not found at {env_path}. "
            "Please create it with VENICE_API_KEY and other required variables."
        )
    load_dotenv(env_path)

def get_api_key():
    """Load and return the VENICE_API_KEY from .env file."""
    load_env()
    api_key = os.getenv("VENICE_API_KEY")
    if not api_key:
        raise ValueError(
            "VENICE_API_KEY not found in .env file. "
            "Please add VENICE_API_KEY=your_key_here to .env"
        )
    return api_key

def get_venice_client():
    """Create and return a configured Venice OpenAI client."""
    # Lazy import - only import OpenAI when this function is called
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("OpenAI library not installed. Install with: pip install openai")
    
    api_key = get_api_key()
    return OpenAI(
        api_key=api_key,
        base_url="https://api.venice.ai/api/v1"
    )

def get_default_model():
    """Get the default Venice model to use."""
    load_env()
    return os.getenv("VENICE_DEFAULT_MODEL", "venice-uncensored")

def get_venice_parameters():
    """Get default Venice parameters from environment or return defaults."""
    load_env()
    return {
        "include_venice_system_prompt": os.getenv("VENICE_INCLUDE_SYSTEM_PROMPT", "true").lower() == "true",
        "enable_web_search": os.getenv("VENICE_ENABLE_WEB_SEARCH", "off"),
        "enable_web_citations": os.getenv("VENICE_ENABLE_WEB_CITATIONS", "false").lower() == "true",
    }

def get_model_for_role(role: str) -> str:
    """
    Retrieves the model name for a given role from the models.json configuration.
    """
    config_path = PROJECT_ROOT / "config" / "models.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            models_config = json.load(f)
        
        role_config = models_config.get("model_roles", {}).get(role)
        if not role_config:
            # Fallback to a default if role is not found
            print(f"Warning: Model role '{role}' not found in config. Falling back to 'llama-3.2-3b'.")
            return "llama-3.2-3b"
        
        return role_config.get("model", "llama-3.2-3b")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading models config: {e}. Falling back to 'llama-3.2-3b'.")
        return "llama-3.2-3b"