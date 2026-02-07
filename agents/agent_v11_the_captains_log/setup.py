#!/usr/bin/env python3
"""
Self-contained setup script for Agent v11: The Captain's Log.
This script creates the persona directory, templates, and config from scratch.
It is updated to reflect the new "Tool-First" architecture.
"""

import json
import sys
from pathlib import Path

# --- Agent-Specific Data ---
PERSONA_NAME = "captains_log"
PERSONA_DESCRIPTION = "A personal journaling agent responsible for maintaining daily logs and weekly reviews in a structured Markdown format."
PERSONA_SYSTEM_PROMPT = """You are 'The Captain's Log', a personal AI journaling assistant. Your tone is professional, efficient, and slightly formal, like a ship's captain recording a log entry. You are responsible for maintaining a user's daily and weekly logs. When you complete a task, report it concisely and clearly."""

# Define the specific config for this agent.
# This is a simplified config that aligns with our new architecture.
AGENT_CONFIG = {
    "name": PERSONA_NAME,
    "role": "user",
    "description": PERSONA_DESCRIPTION,
    "system_prompt": PERSONA_SYSTEM_PROMPT,
    "memory_config": {
        "default_recall_target": "self",
        "fact_expiration_days": 30
    },
    "acl": {
        "can_read": ["captains_log"],
        "can_write": ["captains_log"]
    }
}

# Define the templates for this agent
DAILY_TEMPLATE = """# Daily Log - {{DATE}}

## Mood
-

## Notes & Thoughts

---
#tags: #daily
"""

WEEKLY_TEMPLATE = """# Weekly Review - {{WEEK_START_DATE}} to {{WEEK_END_DATE}}

## Highlights & Wins

## Project Progress Summary
<!-- This section will be auto-populated in a future sprint -->

---
#tags: #weekly #review
"""

def main():
    """Creates the persona directory, templates, and config file."""
    base_path = Path(f"data/personas/{PERSONA_NAME}")
    print(f"--- Initializing Persona: {PERSONA_NAME} ---")
    print(f"Target directory: {base_path.resolve()}")
    
    if base_path.exists():
        print(f"Warning: Persona directory '{base_path}' already exists. This script will overwrite the config and templates.")
        # We will not abort to allow for easy re-initialization of templates/config if they change.
        # sys.exit(1)

    # 1. Create directory structure
    print("\nStep 1: Creating directories...")
    (base_path / "user/daily").mkdir(parents=True, exist_ok=True)
    (base_path / "user/weekly").mkdir(parents=True, exist_ok=True)
    (base_path / "templates").mkdir(parents=True, exist_ok=True)
    print(" - Directories created.")

    # 2. Create templates
    print("\nStep 2: Creating template files...")
    with open(base_path / "templates/daily_template.md", "w") as f:
        f.write(DAILY_TEMPLATE)
    with open(base_path / "templates/weekly_template.md", "w") as f:
        f.write(WEEKLY_TEMPLATE)
    print(" - Templates created.")

    # 3. Create config.json
    print("\nStep 3: Creating config.json...")
    with open(base_path / "config.json", "w") as f:
        json.dump(AGENT_CONFIG, f, indent=2)
    print(" - Config created.")
    
    print("\n✅ Setup complete! You can now run the agent.")

if __name__ == "__main__":
    main()