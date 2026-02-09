#!/usr/bin/env python3
"""
A test script to verify the memory pipeline from ingestion to context synthesis.
This script simulates the Conductor's new role without using the AgentShell or LLM.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from symphony.context_manager import get_context_manager

def main():
    print("--- Testing the Memory Pipeline ---")

    # --- 1. Ingest Data ---
    print("\n[STEP 1] Running ingestion script...")
    ingestion_script = project_root / "agents" / "agent_v13_the_knowledge_base" / "ingest_static_data.py"
    try:
        import subprocess
        result = subprocess.run([sys.executable, str(ingestion_script)], check=True, capture_output=True, text=True)
        print("Ingestion successful.")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        return

    # --- 2. Simulate Conductor Loading Agent ---
    print("\n[STEP 2] Simulating Conductor loading agent and parsing ACL...")
    agent_name = 'Public FAQ Agent'
    # This is what the Conductor would parse from the YAML
    agent_acl = {'access_level': 'public'} 
    print(f"Agent: '{agent_name}'")
    print(f"ACL: {agent_acl}")

    # --- 3. Test ContextManager.get_context() ---
    print("\n[STEP 3] Testing ContextManager.get_context()...")

    # Get the singleton ContextManager instance
    context_manager = get_context_manager()

    # Test Query 1: Should find data from both sources
    query1 = "When is Sarah's birthday and what does my knowledge base say about birthdays?"
    print(f"\nTesting Query 1: '{query1}'")
    context1 = context_manager.get_context(query1, agent_acl)
    print("--- Retrieved Context ---")
    print(context1)
    print("--- End Context ---")

    # Test Query 2: Should be filtered out by ACL
    query2 = "Tell me about Ben."
    print(f"\nTesting Query 2: '{query2}' (Ben has 'internal' access, should return nothing)")
    context2 = context_manager.get_context(query2, agent_acl)
    print("--- Retrieved Context ---")
    print(context2)
    print("--- End Context ---")

    # Test Query 3: Should find nothing
    query3 = "What is the capital of France?"
    print(f"\nTesting Query 3: '{query3}' (Should return nothing)")
    context3 = context_manager.get_context(query3, agent_acl)
    print("--- Retrieved Context ---")
    print(context3)
    print("--- End Context ---")
    
    # --- 4. Clean up ---
    context_manager.close()
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()