#!/usr/bin/env python3
"""
Setup script for the Knowledge Base Agent.
This script copies the agent's persona file to the central personas directory
and runs the ingestion script to populate the memory stores.
"""

import sys
import shutil
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("--- Setting up Knowledge Base Agent ---")
    
    # --- 0. Copy persona file to the central personas directory ---
    personas_dir = project_root / "personas"
    personas_dir.mkdir(exist_ok=True) # Ensure the central directory exists
    
    source_persona = Path(__file__).parent / "persona.yaml"
    target_persona = personas_dir / "agent_v13_the_knowledge_base.yaml"
    
    print(f"Copying persona from '{source_persona}' to '{target_persona}'...")
    shutil.copy(source_persona, target_persona)
    print("Persona file copied successfully.")

    # --- 1. Run the ingestion script ---
    print("Running data ingestion script...")
    ingestion_script = Path(__file__).parent / "ingest_static_data.py"
    
    try:
        # Execute the ingestion script
        result = subprocess.run([sys.executable, str(ingestion_script)], check=True, capture_output=True, text=True)
        print("Ingestion script output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error: Ingestion script failed.")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        sys.exit(1) # Exit with an error code if ingestion fails
    
    print("✅ Knowledge Base Agent setup complete.")

if __name__ == "__main__":
    main()