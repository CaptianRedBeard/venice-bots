import os
import yaml
from pathlib import Path

def setup_default_personas():
    """
    Creates the default persona YAML files in the project's /personas directory.
    This function ensures that the necessary agent configurations are available
    for the Symphony framework, treating them as private user data.
    """
    # --- FIX: Correctly determine the project root directory (three levels up from this script) ---
    project_root = Path(__file__).resolve().parent.parent.parent
    personas_dir = project_root / "personas"

    print(f"Setting up default personas in: {personas_dir}")

    # Create the personas directory if it doesn't exist
    personas_dir.mkdir(parents=True, exist_ok=True)
    print("✓ Personas directory created/verified.")

    # Define the default personas
    default_personas = {
        "researcher_agent": {
            "name": "Researcher Agent",
            "description": "An agent specialized in researching topics and providing concise summaries.",
            "system_prompt": "You are a meticulous researcher. Your task is to investigate the given topic and provide a clear, concise summary of your findings.",
            "default_tools": []  # This agent has no tools by default
        },
        "journaler_agent": {
            "name": "Journaler Agent",
            "description": "An agent that formats provided text into a structured daily log entry.",
            "system_prompt": "You are a journal keeper. Take any text given to you and format it as a daily log entry with a title, date, and clear sections.",
            "default_tools": ["file_system_tool"]  # This agent uses the file system tool
        }
    }

    # Write each persona to its corresponding YAML file
    for persona_name, config in default_personas.items():
        persona_file = personas_dir / f"{persona_name}.yaml"
        if not persona_file.exists():
            with open(persona_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, sort_keys=False, indent=2)
            print(f"✓ Created default persona: {persona_file}")
        else:
            print(f"✓ Persona already exists, skipping: {persona_file}")

    print("\nSetup complete. Default personas are ready.")
    print("IMPORTANT: The '/personas' directory is now in your .gitignore to protect private data.")

if __name__ == "__main__":
    setup_default_personas()